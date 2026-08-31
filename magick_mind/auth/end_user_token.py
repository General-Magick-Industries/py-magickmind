"""Self-refreshing end-user token authentication provider."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable, Dict, Optional

import httpx

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


class EndUserTokenAuth(AuthProvider):
    """Authenticate with an end-user JWT and keep it alive by rotation.

    Rotation goes through ``POST /v1/end-user/tokens/refresh``, which issues a
    fresh token and revokes the presented one. A supervised token (minted with
    ``supervised=True``) is barred from that route; hold one with
    :class:`~magick_mind.auth.static_token.StaticTokenAuth` instead, and let the
    supervisor deliver replacements through :meth:`replace_token`.

    Expiry is read from the token's ``exp`` claim, or from ``expires_in`` on a
    refresh response. Rotation happens lazily inside :meth:`get_token_async`
    once the token is within ``refresh_window_seconds`` of expiring, and can be
    driven proactively by :meth:`keep_fresh` for an agent that only listens.

    Failure taxonomy:

    - ``401`` / ``403`` from the refresh route are verdicts about the credential
      and latch the provider terminal -- every later call raises until
      :meth:`replace_token` supplies a new token.
    - Any other failure is retried on the next call while the current token is
      still valid, and raised only once it has actually expired.
    """

    def __init__(
        self,
        token: str,
        base_url: str,
        *,
        timeout: float = 30.0,
        refresh_window_seconds: float = 120.0,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """
        Args:
            token: The end-user JWT to present
            base_url: Base URL of the Magick Mind API
            timeout: Request timeout for the refresh call, in seconds
            refresh_window_seconds: Rotate once this close to expiry
            ttl_seconds: Lifetime to request on each rotation; server default
                applies if omitted

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
        self._expires_at: Optional[float] = jwt_expiry(token)
        self._terminal: Optional[AuthenticationError] = None
        self._lock = asyncio.Lock()
        self._listeners: list[RotationListener] = []

    @property
    def expires_at(self) -> Optional[float]:
        """Unix timestamp the current token expires at, if known."""
        return self._expires_at

    @property
    def is_terminal(self) -> bool:
        """True once the server has rejected the credential outright."""
        return self._terminal is not None

    def on_rotate(self, listener: RotationListener) -> RotationListener:
        """Register a callback invoked with each new token.

        Used by the realtime client to keep its connect frame current, since a
        rotated-out token is revoked and cannot reconnect.
        """
        self._listeners.append(listener)
        return listener

    def replace_token(self, token: str) -> None:
        """Adopt a token minted out of band, clearing any terminal state."""
        if not token:
            raise ValueError("token is required")
        self._token = token
        self._expires_at = jwt_expiry(token)
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

    async def refresh_if_needed_async(self) -> None:
        if self._terminal is not None:
            raise self._terminal
        if not self._needs_rotation(time.time()):
            return
        async with self._lock:
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
        expire. Run this as a background task alongside such a listener.
        """
        while stop is None or not stop.is_set():
            if self._expires_at is None:
                return
            delay = max(self._expires_at - self.refresh_window_seconds - time.time(), 0)
            if stop is None:
                await asyncio.sleep(delay)
            else:
                try:
                    await asyncio.wait_for(stop.wait(), timeout=delay)
                    return
                except asyncio.TimeoutError:
                    pass
            await self.refresh_if_needed_async()

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

        if response.status_code < 400:
            minted = MintEndUserTokenResponse.model_validate(response.json())
            self._token = minted.token
            self._expires_at = (
                time.time() + minted.expires_in
                if minted.expires_in is not None
                else jwt_expiry(minted.token)
            )
            self._notify()
            return

        status = response.status_code
        if status == 401:
            self._terminal = TokenExpiredError("End-user token rejected on rotation")
            self._terminal.status_code = 401
            raise self._terminal
        if status == 403:
            self._terminal = AuthenticationError(
                "Rotation refused: the token is supervised or revoked", status_code=403
            )
            raise self._terminal
        self._defer_or_raise(
            AuthenticationError(
                f"Token rotation failed: HTTP {status}", status_code=status
            )
        )

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
