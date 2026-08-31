"""Main Magick Mind SDK client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from openai import AsyncOpenAI

from magick_mind.auth import (
    AuthProvider,
    EmailPasswordAuth,
    EndUserTokenAuth,
    StaticTokenAuth,
)
from magick_mind.config import SDKConfig
from magick_mind.exceptions import MagickMindError
from magick_mind.http import HTTPClient
from magick_mind.realtime import RealtimeClient
from magick_mind.resources.v1.chat import ChatResourceV1
from magick_mind.resources.v1.magickspaces import MagickspacesResourceV1
from magick_mind.resources.v1.mindspace import MindspaceResourceV1
from magick_mind.resources.v2.reason import ReasonResourceV2


class MagickMind:
    """
    Main client for the Magick Mind SDK.

    This is the primary interface for interacting with the Magick Mind API.

    Provides:
    - Authentication (email/password with JWT, automatic refresh)
    - Typed resources (v1.chat, etc.) with Pydantic validation
    - HTTP client for direct API access
    - Realtime client for WebSocket connections (async)

    Example:
        # Initialize client
        client = MagickMind(
            email="user@example.com",
            password="your_password",
            base_url="https://api.magickmind.ai"
        )

        # Use typed resources (recommended)
        response = client.v1.chat.send(
            api_key="sk-...",
            mindspace_id="mind-123",
            message="Hello!",
            sender_id="user-456"
        )
        print(response.content.content)  # AI response

        # Or use convenience alias
        response = client.chat.send(...)
        magickspaces = await client.magickspaces.list()

        # Use HTTP client directly for experimental endpoints
        response = client.http.post("/experimental/endpoint", json={...})

        # Use Realtime client (in async context)
        async def main():
            await client.realtime.connect()
            await client.realtime.subscribe(target_user_id="user-456")
    """

    def __init__(
        self,
        base_url: str,
        email: str,
        password: str,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        ws_endpoint: Optional[str] = None,
    ):
        """
        Initialize the Magick Mind client.

        Args:
            base_url: Base URL of the Magick Mind API (e.g., https://api.magickmind.ai)
            email: User email for authentication
            password: User password for authentication
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            ws_endpoint: WebSocket URL (Required for .realtime usage)
        """
        if not email or not password:
            raise ValueError("Email and password are required for authentication")

        config = SDKConfig(
            base_url=base_url,
            timeout=timeout,
            verify_ssl=verify_ssl,
            ws_endpoint=ws_endpoint,
        )
        auth = EmailPasswordAuth(
            email=email, password=password, base_url=base_url, timeout=timeout
        )
        self._wire(config, auth, ws_endpoint, end_user=False)

    def _wire(
        self,
        config: SDKConfig,
        auth: AuthProvider,
        ws_endpoint: Optional[str],
        *,
        end_user: bool,
    ) -> None:
        """Build the HTTP, realtime, and resource graph around an auth provider."""
        self.config: SDKConfig = config
        self.auth: AuthProvider = auth

        # Create HTTP client (private, accessed via property)
        self._http = HTTPClient(config=self.config, auth=self.auth)

        # Create Realtime client (private, accessed via property)
        self._realtime = RealtimeClient(
            auth=self.auth, ws_url=ws_endpoint, end_user=end_user
        )

        # Initialize typed resources
        from magick_mind.resources import V1Resources, V2Resources

        self.v1: V1Resources = V1Resources(self._http)
        self.v2: V2Resources = V2Resources(self._http)

        # Convenience alias for default version
        self.chat: ChatResourceV1 = self.v1.chat
        self.magickspaces: MagickspacesResourceV1 = self.v1.magickspaces
        self.mindspace: MindspaceResourceV1 = self.v1.mindspace
        self.reason: ReasonResourceV2 = self.v2.reason

    @classmethod
    def from_token(
        cls,
        base_url: str,
        token: str,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        ws_endpoint: Optional[str] = None,
        *,
        refresh: bool = False,
        refresh_window_seconds: float = 120.0,
    ) -> MagickMind:
        """
        Build a client that authenticates with a pre-issued end-user token.

        This is how an agent process uses an end-user JWT minted for it by a
        service user (``client.v1.end_user.mint_token()``). Such a token is the
        credential for the end-user API surface, where the caller is identified
        by the token subject rather than by an ID in the request -- the
        ``*_own`` methods (``v1.persona.prepare_for_own_agent()``,
        ``v1.magickspaces.send_own_message()``, ``v1.episode.process_own()``,
        ...). ``.realtime`` connects as the end user and receives magickspace
        fan-out on the agent's own ``user:`` channel.

        The token is not inspected or validated here. Only the server decides
        whether it is acceptable, so a wrong-kind, expired, or revoked token
        surfaces as a 401 on the first call rather than at construction.

        Args:
            base_url: Base URL of the Magick Mind API
            token: End-user JWT to present on every request
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            ws_endpoint: WebSocket URL (required for ``.realtime`` usage)
            refresh: Keep the token alive by rotating it through
                ``POST /v1/end-user/tokens/refresh`` ahead of expiry (see
                :class:`~magick_mind.auth.EndUserTokenAuth`). Leave ``False``
                for a token minted with ``supervised=True`` -- the server bars
                it from that route -- and for any token whose lifecycle a
                control plane owns; such a client uses the token as given
                and never refreshes it.
            refresh_window_seconds: With ``refresh``, rotate once this close
                to expiry

        Returns:
            A MagickMind client bound to the token

        Raises:
            ValueError: If the token is empty

        Example:
            minted = await client.v1.end_user.mint_token(agent_id)
            agent = MagickMind.from_token(BASE_URL, minted.token, refresh=True)
            prepared = await agent.v1.persona.prepare_for_own_agent()
        """
        self = cls.__new__(cls)
        config = SDKConfig(
            base_url=base_url,
            timeout=timeout,
            verify_ssl=verify_ssl,
            ws_endpoint=ws_endpoint,
        )
        auth: AuthProvider = (
            EndUserTokenAuth(
                token,
                base_url,
                timeout=timeout,
                refresh_window_seconds=refresh_window_seconds,
            )
            if refresh
            else StaticTokenAuth(token)
        )
        self._wire(config, auth, ws_endpoint, end_user=True)
        return self

    @property
    def http(self) -> HTTPClient:
        """
        Low-level HTTP client bound to this MagickMind instance.

        Features:
        - Uses same base_url and configuration
        - Automatically attaches authentication tokens
        - Applies centralized error mapping
        - Auto-refreshes expired tokens

        Intended for:
        - Developers testing new endpoints
        - Power users needing direct API access
        - Experimenting with endpoints before implementing resources

        Example:
            # Test a new endpoint directly
            response = client.http.post(
                "/experimental/new-feature",
                json={"test": "data"}
            )

            # Quick one-off calls
            response = client.http.get("/v1/status")

        Returns:
            HTTPClient: Configured HTTP client instance
        """
        return self._http

    @property
    def realtime(self) -> RealtimeClient:
        """
        Realtime WebSocket client.

        Note: This client is ASYNC. You must use it within an async context.

        Features:
        - Authenticated WebSocket connection
        - RPC subscriptions
        - Handling disconnects/reconnects (via centrifuge-python)

        Returns:
            RealtimeClient: Configured async realtime client
        """
        return self._realtime

    async def get_user_id(self) -> str:
        """
        The authenticated user's ID (JWT ``sub`` claim).

        Useful for subscribing to your own realtime events::

            user_id = await client.get_user_id()
            await client.realtime.subscribe(target_user_id=user_id)

        Raises:
            MagickMindError: If the current token does not contain a ``sub`` claim
                or cannot be decoded.
        """
        from magick_mind.auth.jwt import jwt_subject

        token = await self.auth.get_token_async()
        uid = jwt_subject(token)
        if not uid:
            raise MagickMindError("Failed to extract user_id from JWT token")
        return uid

    async def test_connection(self) -> bool:
        """Test the connection to the API."""
        try:
            # This assumes there's a health check or similar endpoint
            response = await self.http.get("/health")
            return response.get("success", False)
        except Exception:
            return False

    def is_authenticated(self) -> bool:
        """
        Check if the client is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self.auth.is_authenticated()

    async def close(self) -> None:
        """Close the client and cleanup resources."""
        await self._http.close()
        await self._realtime.disconnect()

    async def __aenter__(self) -> MagickMind:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc_val: object,
        exc_tb: object,
    ) -> None:
        """Async context manager exit."""
        await self.close()

    def openai_client(self, api_key: str, compute_power: int = 1) -> AsyncOpenAI:
        """
        Return a pre-configured AsyncOpenAI client pointed at the Magick Mind API.

        The API exposes an OpenAI-compatible endpoint at /v1/chat/completions.
        Auth is a Bearer api_key (not JWT). Pass the api_key you want to use.

        Usage::

            oai = client.openai_client(api_key="sk-...")
            resp = await oai.chat.completions.create(
                model="openrouter/meta-llama/llama-4-maverick",
                messages=[{"role": "user", "content": "hello"}],
            )

        Args:
            api_key: API key passed as Bearer token.
            compute_power: X-Compute-Power header value (default 1).

        Returns:
            AsyncOpenAI: Pre-configured client pointed at the Magick Mind /v1 API.

        Raises:
            ImportError: If the ``openai`` package is not installed.
                Install with: ``pip install magick-mind[openai]``
        """
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError(
                "openai package required. Install with: pip install magickmind[openai]"
            )
        return AsyncOpenAI(
            api_key=api_key,
            base_url=f"{self.config.normalized_base_url()}/v1",
            default_headers={"X-Compute-Power": str(compute_power)},
        )

    def __repr__(self) -> str:
        """String representation of the client."""
        return (
            f"MagickMind(base_url='{self.config.base_url}', "
            f"auth='{type(self.auth).__name__}')"
        )
