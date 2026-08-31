"""Tests for EndUserTokenAuth rotation and MagickMind.from_token(refresh=True)."""

from __future__ import annotations

import asyncio
import base64
import json
import time

import pytest
from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.auth import EndUserTokenAuth, StaticTokenAuth
from magick_mind.auth.jwt import decode_jwt_claims, jwt_expiry, jwt_subject
from magick_mind.exceptions import AuthenticationError, TokenExpiredError

BASE_URL = "https://api.test"
REFRESH_URL = f"{BASE_URL}/v1/end-user/tokens/refresh"


def _jwt(sub: str = "agent-1", exp: float | None = None) -> str:
    def seg(d: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()

    claims: dict = {"sub": sub, "token_use": "end_user"}
    if exp is not None:
        claims["exp"] = int(exp)
    return f"{seg({'alg': 'HS256'})}.{seg(claims)}.sig"


def _minted(token: str, expires_in: int = 3600) -> dict:
    return {
        "token": token,
        "expires_at": "2026-09-01T00:00:00Z",
        "token_type": "Bearer",
        "expires_in": expires_in,
    }


class TestJwtHelpers:
    def test_reads_claims_without_verifying(self):
        token = _jwt("agent-7", exp=1_800_000_000)
        assert decode_jwt_claims(token)["sub"] == "agent-7"
        assert jwt_subject(token) == "agent-7"
        assert jwt_expiry(token) == 1_800_000_000.0

    def test_tolerates_garbage(self):
        assert decode_jwt_claims("not-a-jwt") == {}
        assert jwt_subject("a.b") is None
        assert jwt_expiry(_jwt("x")) is None


class TestEndUserTokenAuth:
    async def test_serves_token_without_rotating_while_fresh(
        self, httpx_mock: HTTPXMock
    ):
        auth = EndUserTokenAuth(_jwt(exp=time.time() + 3600), BASE_URL)

        assert await auth.get_headers_async() == {
            "Authorization": f"Bearer {await auth.get_token_async()}"
        }
        assert auth.is_authenticated()
        assert httpx_mock.get_requests() == []

    async def test_rotates_inside_the_refresh_window(self, httpx_mock: HTTPXMock):
        old = _jwt(exp=time.time() + 60)
        new = _jwt(exp=time.time() + 3600)
        httpx_mock.add_response(url=REFRESH_URL, method="POST", json=_minted(new))
        auth = EndUserTokenAuth(old, BASE_URL, refresh_window_seconds=120)
        seen: list[str] = []
        auth.on_rotate(seen.append)

        assert await auth.get_token_async() == new

        request = httpx_mock.get_requests()[-1]
        assert request.headers["Authorization"] == f"Bearer {old}"
        assert json.loads(request.content) == {}
        assert seen == [new]
        assert auth.expires_at is not None and auth.expires_at > time.time() + 3000

    async def test_sends_requested_ttl(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=REFRESH_URL, method="POST", json=_minted(_jwt(exp=time.time() + 900))
        )
        auth = EndUserTokenAuth(_jwt(exp=time.time() + 10), BASE_URL, ttl_seconds=900)

        await auth.get_token_async()

        assert json.loads(httpx_mock.get_requests()[-1].content) == {"ttl_seconds": 900}

    async def test_rotation_is_single_flight(self, httpx_mock: HTTPXMock):
        """Concurrent callers must not each rotate: the second rotation would
        present a token the first one just revoked."""
        new = _jwt(exp=time.time() + 3600)
        httpx_mock.add_response(url=REFRESH_URL, method="POST", json=_minted(new))
        auth = EndUserTokenAuth(_jwt(exp=time.time() + 10), BASE_URL)

        tokens = await asyncio.gather(*(auth.get_token_async() for _ in range(5)))

        assert set(tokens) == {new}
        assert len(httpx_mock.get_requests()) == 1

    @pytest.mark.parametrize(
        ("status", "error"), [(401, TokenExpiredError), (403, AuthenticationError)]
    )
    async def test_credential_verdicts_latch_terminal(
        self, httpx_mock: HTTPXMock, status: int, error: type[Exception]
    ):
        httpx_mock.add_response(url=REFRESH_URL, method="POST", status_code=status)
        auth = EndUserTokenAuth(_jwt(exp=time.time() + 10), BASE_URL)

        with pytest.raises(error):
            await auth.get_token_async()

        assert auth.is_terminal
        assert not auth.is_authenticated()
        with pytest.raises(error):
            await auth.get_headers_async()
        assert len(httpx_mock.get_requests()) == 1, "a dead credential is not retried"

    async def test_transient_failure_keeps_serving_a_valid_token(
        self, httpx_mock: HTTPXMock
    ):
        old = _jwt(exp=time.time() + 60)
        httpx_mock.add_response(url=REFRESH_URL, method="POST", status_code=503)
        auth = EndUserTokenAuth(old, BASE_URL)

        assert await auth.get_token_async() == old
        assert not auth.is_terminal

    async def test_transient_failure_raises_once_expired(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=REFRESH_URL, method="POST", status_code=503)
        auth = EndUserTokenAuth(_jwt(exp=time.time() - 1), BASE_URL)

        with pytest.raises(AuthenticationError):
            await auth.get_token_async()
        assert not auth.is_terminal

    async def test_replace_token_clears_terminal_state(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=REFRESH_URL, method="POST", status_code=401)
        auth = EndUserTokenAuth(_jwt(exp=time.time() + 10), BASE_URL)
        with pytest.raises(TokenExpiredError):
            await auth.get_token_async()

        fresh = _jwt(exp=time.time() + 3600)
        auth.replace_token(fresh)

        assert not auth.is_terminal
        assert await auth.get_token_async() == fresh

    async def test_unknown_expiry_never_rotates(self, httpx_mock: HTTPXMock):
        auth = EndUserTokenAuth("opaque-token", BASE_URL)

        assert await auth.get_token_async() == "opaque-token"
        assert auth.is_authenticated()
        assert httpx_mock.get_requests() == []

    async def test_keep_fresh_rotates_ahead_of_expiry(self, httpx_mock: HTTPXMock):
        new = _jwt(exp=time.time() + 3600)
        httpx_mock.add_response(url=REFRESH_URL, method="POST", json=_minted(new))
        auth = EndUserTokenAuth(
            _jwt(exp=time.time() + 0.2), BASE_URL, refresh_window_seconds=0.1
        )
        stop = asyncio.Event()
        task = asyncio.create_task(auth.keep_fresh(stop))

        for _ in range(50):
            if httpx_mock.get_requests():
                break
            await asyncio.sleep(0.02)
        stop.set()
        await asyncio.wait_for(task, timeout=1)

        assert len(httpx_mock.get_requests()) == 1
        assert await auth.get_token_async() == new

    def test_rejects_empty_token(self):
        with pytest.raises(ValueError):
            EndUserTokenAuth("", BASE_URL)


class TestFromTokenRefresh:
    def test_default_is_static(self):
        client = MagickMind.from_token(BASE_URL, "jwt-abc")
        assert isinstance(client.auth, StaticTokenAuth)
        assert client.realtime.end_user is True

    def test_refresh_uses_rotating_auth(self):
        client = MagickMind.from_token(BASE_URL, _jwt(), refresh=True)
        assert isinstance(client.auth, EndUserTokenAuth)
        assert client.realtime.end_user is True
        assert "EndUserTokenAuth" in repr(client)

    async def test_rotated_token_is_used_on_the_next_call(self, httpx_mock: HTTPXMock):
        new = _jwt(exp=time.time() + 3600)
        httpx_mock.add_response(url=REFRESH_URL, method="POST", json=_minted(new))
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/magickspaces",
            method="GET",
            json={
                "data": [],
                "paging": {
                    "cursors": {"after": None, "before": None},
                    "has_more": False,
                    "has_previous": False,
                },
            },
        )
        client = MagickMind.from_token(
            BASE_URL, _jwt(exp=time.time() + 10), refresh=True
        )

        await client.v1.magickspaces.list_own()

        listing = httpx_mock.get_requests()[-1]
        assert listing.headers["Authorization"] == f"Bearer {new}"
        await client.close()
