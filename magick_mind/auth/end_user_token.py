"""Self-refreshing end-user token authentication provider."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable, Dict, NoReturn, Optional

import httpx
from pydantic import ValidationError as PydanticValidationError

from magick_mind.auth.base import AuthProvider
from magick_mind.auth.jwt import jwt_expiry
from magick_mind.exceptions import AuthenticationError, TokenExpiredError
from magick_mind.models.v1.end_user import (
    MintEndUserTokenResponse,
    RefreshEndUserTokenRequest,
)
from magick_mind.routes import Routes

logger: logging.Logger = logging.getLogger(__name__)

RotationListener = Callable[[str], None]

PROBLEM_CREDENTIAL_SUPERVISED = "https://bifrost.gmi/problems/credential-supervised"
PROBLEM_CREDENTIAL_REVOKED = "https://bifrost.gmi/problems/credential-revoked"
PROBLEM_CHAIN_REVOKED = "https://bifrost.gmi/problems/chain-revoked"

# Retry pacing for a rotation that failed without a verdict on the credential.
# The server budgets refresh attempts per hour and counts rejected ones, so an
# unpaced retry loop would spend the whole allowance on one outage.
ROTATION_BACKOFF_BASE = 1.0
ROTATION_BACKOFF_MAX = 120.0


def _problem(response: httpx.Response) -> tuple[str, Optional[str]]:
    """Best-effort ``(detail, type)`` from an RFC 7807 or legacy error body."""
    try:
        data = response.json()
    except ValueError:
        return response.reason_phrase or f"HTTP {response.status_code}", None
    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict):
            detail = error.get("detail") or error.get("title") or ""
            problem_type = error.get("type")
            return str(detail), problem_type if isinstance(problem_type, str) else None
        if isinstance(data.get("message"), str):
            return data["message"], None
    return response.reason_phrase or f"HTTP {response.status_code}", None


class EndUserTokenAuth(AuthProvider):
    """Authenticate with an end-user JWT and keep it alive by rotation.

    Rotation goes through ``POST /v1/end-user/tokens/refresh``, which issues a
    fresh token and revokes the presented one. A supervised token (minted with
    ``supervised=True``) is barred from that route; hold one with
    :class:`~magick_mind.auth.static_token.StaticTokenAuth` instead, and let the
    supervisor deliver replacements through :meth:`replace_token`.

    Expiry is read from the token's ``exp`` claim, from ``expires_in`` passed at
    construction, or from ``expires_in`` on a refresh response. Rotation happens
    lazily inside :meth:`get_token_async` once the token is within
    ``refresh_window_seconds`` of expiring, and can be driven proactively by
    :meth:`keep_fresh` for an agent that only listens.

    The chain is finite: the server caps how long a token may keep refreshing
    from its original mint and how long it may sit idle between refreshes. When
    either limit is hit the credential is terminal here too, and only a fresh
    mint from the control plane (delivered with :meth:`replace_token`) recovers
    it.

    Failure taxonomy:

    - ``401``, a ``403`` the server explains (supervised token), or a refresh
      whose response cannot be read (the presented token is already revoked
      by then) latch the provider terminal -- every later call raises until
      :meth:`replace_token` supplies a new token. :attr:`terminal_reason`
      carries the server's explanation.
    - Any other failure is retried while the current token is still valid,
      with exponential backoff inside :meth:`keep_fresh`, and raised only once
      the token has actually expired.
    """

    def __init__(
        self,
        token: str,
        base_url: str,
        *,
        timeout: float = 30.0,
        refresh_window_seconds: float = 120.0,
        ttl_seconds: Optional[int] = None,
        expires_in: Optional[float] = None,
    ) -> None:
        """
        Args:
            token: The end-user JWT to present
            base_url: Base URL of the Magick Mind API
            timeout: Request timeout for the refresh call, in seconds
            refresh_window_seconds: Rotate once this close to expiry
            ttl_seconds: Lifetime to request on each rotation; server default
                applies if omitted
            expires_in: Seconds until ``token`` expires, as reported by the
                mint response; overrides the token's own ``exp`` claim

        Raises:
            ValueError: If the token is empty
        """
        if not token:
            raise ValueError("token is required")
        self.base_url: str = base_url.rstrip("/")
        self.timeout: float = timeout
        self.refresh_window_seconds: float = refresh_window_seconds
        self.ttl_seconds: Optional[int] = ttl_seconds

        self._token: str = token
        self._expires_at: Optional[float] = (
            time.time() + expires_in if expires_in is not None else jwt_expiry(token)
        )
        self._terminal: Optional[tuple[type[AuthenticationError], str, int]] = None
        self._lock = asyncio.Lock()
        self._listeners: list[RotationListener] = []
        if self._expires_at is None:
            logger.warning(
                "End-user token carries no exp claim and no expires_in was given; "
                "it will never be rotated"
            )

    @property
    def expires_at(self) -> Optional[float]:
        """Unix timestamp the current token expires at, if known."""
        return self._expires_at

    @property
    def is_terminal(self) -> bool:
        """True once the server has rejected the credential outright."""
        return self._terminal is not None

    @property
    def terminal_reason(self) -> Optional[str]:
        """Why the credential is terminal, as the server explained it."""
        return self._terminal[1] if self._terminal is not None else None

    def on_rotate(self, listener: RotationListener) -> RotationListener:
        """Register a callback invoked with each new token.

        Used by the realtime client to keep its connect frame current, since a
        rotated-out token is revoked and cannot reconnect.
        """
        self._listeners.append(listener)
        return listener

    def replace_token(self, token: str, *, expires_in: Optional[float] = None) -> None:
        """Adopt a token minted out of band, clearing any terminal state."""
        if not token:
            raise ValueError("token is required")
        self._token = token
        self._expires_at = (
            time.time() + expires_in if expires_in is not None else jwt_expiry(token)
        )
        self._terminal = None
        self._notify()

    def is_authenticated(self) -> bool:
        if self._terminal is not None:
            return False
        if self._expires_at is None:
            return True
        return time.time() < self._expires_at

    def _needs_rotation(self, now: float) -> bool:
        if self._expires_at is None:
            return False
        return now >= self._expires_at - self.refresh_window_seconds

    def _raise_terminal(self) -> None:
        if self._terminal is not None:
            error_type, message, status = self._terminal
            raise error_type(message, status_code=status)

    async def refresh_if_needed_async(self) -> None:
        self._raise_terminal()
        if not self._needs_rotation(time.time()):
            return
        async with self._lock:
            self._raise_terminal()
            if not self._needs_rotation(time.time()):
                return
            await self._rotate()

    async def get_token_async(self) -> str:
        await self.refresh_if_needed_async()
        return self._token

    async def get_headers_async(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {await self.get_token_async()}"}

    async def keep_fresh(self, stop: Optional[asyncio.Event] = None) -> None:
        """Rotate ahead of expiry until ``stop`` is set or the credential dies.

        An agent that only listens on a websocket never calls
        :meth:`get_token_async`, so lazy rotation alone would let its token
        expire. Run this as a background task alongside such a listener, and
        keep a reference to the task: it raises :class:`AuthenticationError`
        when the credential becomes terminal or expires unrotated.
        """
        if self._expires_at is None:
            logger.warning(
                "Token expiry is unknown; keep_fresh cannot schedule rotation"
            )
            return
        failures = 0
        while stop is None or not stop.is_set():
            if self._expires_at is None:
                return
            delay = max(
                self._expires_at - self.refresh_window_seconds - time.time(), 0.0
            )
            if failures:
                backoff = min(
                    ROTATION_BACKOFF_BASE * 2 ** (failures - 1), ROTATION_BACKOFF_MAX
                )
                delay = max(delay, backoff)
            if await self._sleep_or_stop(stop, delay):
                return
            if not self._needs_rotation(time.time()):
                continue
            expiry_before = self._expires_at
            await self.refresh_if_needed_async()
            failures = 0 if self._expires_at != expiry_before else failures + 1

    @staticmethod
    async def _sleep_or_stop(stop: Optional[asyncio.Event], delay: float) -> bool:
        if stop is None:
            await asyncio.sleep(delay)
            return False
        try:
            await asyncio.wait_for(stop.wait(), timeout=delay)
            return True
        except asyncio.TimeoutError:
            return False

    async def _rotate(self) -> None:
        url = f"{self.base_url}{Routes.END_USER_TOKENS_REFRESH}"
        body = RefreshEndUserTokenRequest(ttl_seconds=self.ttl_seconds).model_dump(
            exclude_none=True
        )
        headers = {"Authorization": f"Bearer {self._token}"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=body, headers=headers)
        except httpx.RequestError as e:
            self._defer_or_raise(
                AuthenticationError(f"Network error during token rotation: {e}")
            )
            return

        status = response.status_code
        if 200 <= status < 300:
            try:
                minted = MintEndUserTokenResponse.model_validate(response.json())
            except (ValueError, PydanticValidationError) as e:
                # The server revoked the presented token to mint its successor;
                # a successor we cannot read is a lost credential, not a retry.
                self._latch(
                    AuthenticationError,
                    f"Token rotation returned an unreadable response: {e}",
                    status,
                )
            self._token = minted.token
            self._expires_at = (
                time.time() + minted.expires_in
                if minted.expires_in is not None
                else jwt_expiry(minted.token)
            )
            self._notify()
            return

        detail, problem_type = _problem(response)
        if status == 401:
            self._latch(
                TokenExpiredError, f"End-user token rejected on rotation: {detail}", 401
            )
        if status == 403 and problem_type is not None:
            message = (
                "A supervised token cannot refresh itself; its supervisor mints replacements"
                if problem_type == PROBLEM_CREDENTIAL_SUPERVISED
                else f"Rotation refused: {detail}"
            )
            self._latch(AuthenticationError, message, 403)
        self._defer_or_raise(
            AuthenticationError(
                f"Token rotation failed: HTTP {status}: {detail}", status_code=status
            )
        )

    def _latch(
        self, error_type: type[AuthenticationError], message: str, status: int
    ) -> NoReturn:
        self._terminal = (error_type, message, status)
        raise error_type(message, status_code=status)

    def _defer_or_raise(self, error: AuthenticationError) -> None:
        if self._expires_at is not None and time.time() < self._expires_at:
            logger.warning("%s; retrying on the next call", error)
            return
        raise error

    def _notify(self) -> None:
        for listener in self._listeners:
            try:
                listener(self._token)
            except Exception:
                logger.exception("Token rotation listener failed")
