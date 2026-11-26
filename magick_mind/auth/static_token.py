"""Static bearer-token authentication provider."""

from __future__ import annotations

from typing import Dict

from magick_mind.auth.base import AuthProvider


class StaticTokenAuth(AuthProvider):
    """Authenticate with a pre-issued bearer token.

    Unlike :class:`~magick_mind.auth.email_password.EmailPasswordAuth`, this
    provider holds a token it did not obtain and cannot renew: there is no
    login to repeat and no refresh token to exchange. When the token expires
    the server rejects it, and the holder must be given a new one.

    This is the credential an agent process uses -- typically an end-user JWT
    minted by a service user via ``client.v1.end_user.mint_token()``.
    """

    def __init__(self, token: str) -> None:
        """
        Args:
            token: The bearer token to present on every request

        Raises:
            ValueError: If the token is empty
        """
        if not token:
            raise ValueError("token is required")
        self._token = token

    async def get_headers_async(self) -> Dict[str, str]:
        """Authorization header carrying the token."""
        return {"Authorization": f"Bearer {self._token}"}

    async def refresh_if_needed_async(self) -> None:
        """No-op: a static token cannot be refreshed."""
        return None

    def is_authenticated(self) -> bool:
        """True whenever a token is held.

        This reports possession, not validity -- the token may be expired or
        revoked, which only the server can determine.
        """
        return bool(self._token)

    async def get_token_async(self) -> str:
        """The raw token."""
        return self._token
