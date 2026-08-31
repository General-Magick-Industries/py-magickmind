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
from magick_mind.auth.end_user_token import (
    PROBLEM_CHAIN_REVOKED,
    PROBLEM_CREDENTIAL_SUPERVISED,
)
from magick_mind.auth.jwt import (
    AUDIENCE_SUPERVISED,
    decode_jwt_claims,
    jwt_audience,
    jwt_expiry,
    jwt_subject,
)
from magick_mind.exceptions import AuthenticationError, TokenExpiredError

BASE_URL = "https://api.test"
REFRESH_URL = f"{BASE_URL}/v1/end-user/tokens/refresh"


def _jwt(sub: str = "agent-1", exp: float | None = None, aud: str | None = None) -> str:
    def seg(d: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()

    claims: dict = {"sub": sub, "token_use": "end_user"}
    if exp is not None:
        claims["exp"] = int(exp)
    if aud is not None:
        claims["aud"] = [aud]
    return f"{seg({'alg': 'HS256'})}.{seg(claims)}.sig"


def _problem(status: int, detail: str, problem_type: str) -> dict:
    return {
        "error": {
            "type": problem_type,
            "title": "Error",
            "status": status,
            "detail": detail,
        }
    }


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
        assert jwt_audience("a.b") == []

    def test_reads_audience(self):
        assert jwt_audience(_jwt(aud=AUDIENCE_SUPERVISED)) == [AUDIENCE_SUPERVISED]


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
        ("status", "body", "error", "reason"),
        [
            (401, None, TokenExpiredError, "Unauthorized"),
            (
                401,
                _problem(
                    401,
                    "token chain idle too long; re-authenticate",
                    PROBLEM_CHAIN_REVOKED,
                ),
                TokenExpiredError,
                "idle too long",
            ),
            (
                403,
                _problem(403, "supervisor-managed", PROBLEM_CREDENTIAL_SUPERVISED),
                AuthenticationError,
                "supervised token cannot refresh itself",
            ),
        ],
    )
    async def test_credential_verdicts_latch_terminal(
        self,
        httpx_mock: HTTPXMock,
        status: int,
        body: dict | None,
        error: type[Exception],
        reason: str,
    ):
        httpx_mock.add_response(
            url=REFRESH_URL, method="POST", status_code=status, json=body
        )
        auth = EndUserTokenAuth(_jwt(exp=time.time() + 10), BASE_URL)

        with pytest.raises(error) as first:
            await auth.get_token_async()

        assert reason in str(first.value)
        assert auth.is_terminal
        assert auth.terminal_reason is not None and reason in auth.terminal_reason
        assert not auth.is_authenticated()
        with pytest.raises(error) as second:
            await auth.get_headers_async()
        assert second.value is not first.value, "each raise is a fresh instance"
        assert len(httpx_mock.get_requests()) == 1, "a dead credential is not retried"

    async def test_unexplained_403_is_retried_not_latched(self, httpx_mock: HTTPXMock):
        """A proxy or WAF 403 carries no problem type; only Bifrost's verdicts latch."""
        old = _jwt(exp=time.time() + 60)
        httpx_mock.add_response(url=REFRESH_URL, method="POST", status_code=403)
        auth = EndUserTokenAuth(old, BASE_URL)

        assert await auth.get_token_async() == old
        assert not auth.is_terminal

    @pytest.mark.parametrize(
        "kwargs",
        [{"text": "<html>captive portal</html>"}, {"json": {"expires_at": "x"}}],
    )
    async def test_unreadable_success_latches_terminal(
        self, httpx_mock: HTTPXMock, kwargs: dict
    ):
        """The server revoked the presented token to mint the successor; a
        successor we cannot read is a lost credential, not a retry."""
        httpx_mock.add_response(
            url=REFRESH_URL, method="POST", status_code=200, **kwargs
        )
        auth = EndUserTokenAuth(_jwt(exp=time.time() + 10), BASE_URL)

        with pytest.raises(AuthenticationError, match="unreadable"):
            await auth.get_token_async()
        assert auth.is_terminal

    async def test_expires_in_seeds_expiry_for_a_token_without_exp(self):
        auth = EndUserTokenAuth(_jwt(), BASE_URL, expires_in=300)
        assert auth.expires_at is not None
        assert 290 < auth.expires_at - time.time() <= 300

    async def test_keep_fresh_backs_off_after_a_transient_failure(
        self, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ):
        """Inside the refresh window a failed rotation must not be retried in a
        tight loop: the server counts rejected attempts against the budget."""
        import magick_mind.auth.end_user_token as module

        monkeypatch.setattr(module, "ROTATION_BACKOFF_BASE", 0.05)
        httpx_mock.add_response(
            url=REFRESH_URL, method="POST", status_code=503, is_reusable=True
        )
        auth = EndUserTokenAuth(
            _jwt(exp=time.time() + 5), BASE_URL, refresh_window_seconds=10
        )
        stop = asyncio.Event()
        task = asyncio.create_task(auth.keep_fresh(stop))

        await asyncio.sleep(0.4)
        stop.set()
        await asyncio.wait_for(task, timeout=1)

        attempts = len(httpx_mock.get_requests())
        assert 1 <= attempts <= 6, f"{attempts} attempts in 0.4s is not backing off"

    async def test_keep_fresh_returns_when_expiry_is_unknown(
        self, httpx_mock: HTTPXMock, caplog: pytest.LogCaptureFixture
    ):
        auth = EndUserTokenAuth("opaque-token", BASE_URL)

        with caplog.at_level("WARNING"):
            await asyncio.wait_for(auth.keep_fresh(asyncio.Event()), timeout=1)

        assert "cannot schedule rotation" in caplog.text
        assert httpx_mock.get_requests() == []

    async def test_transient_failure_keeps_serving_a_valid_token(
        self, httpx_mock: HTTPXMock
    ):
        old = _jwt(exp=time.time() + 60)
        httpx_mock.add_response(
            url=REFRESH_URL, method="POST", status_code=503, is_reusable=True
        )
        auth = EndUserTokenAuth(old, BASE_URL)

        assert await auth.get_token_async() == old
        assert not auth.is_terminal

    async def test_transient_failure_raises_once_expired(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=REFRESH_URL, method="POST", status_code=503, is_reusable=True
        )
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
    def test_default_follows_the_audience(self):
        """Bifrost marks supervised tokens in `aud`; anything else may refresh."""
        supervised = MagickMind.from_token(BASE_URL, _jwt(aud=AUDIENCE_SUPERVISED))
        assert isinstance(supervised.auth, StaticTokenAuth)
        assert supervised.end_user_auth is None

        self_managed = MagickMind.from_token(BASE_URL, _jwt(aud="end_user_self"))
        assert isinstance(self_managed.auth, EndUserTokenAuth)
        assert self_managed.end_user_auth is self_managed.auth

        unmarked = MagickMind.from_token(BASE_URL, "jwt-abc")
        assert isinstance(unmarked.auth, EndUserTokenAuth)
        assert unmarked.realtime.end_user is True

    def test_explicit_refresh_overrides_the_audience(self):
        static = MagickMind.from_token(
            BASE_URL, _jwt(aud="end_user_self"), refresh=False
        )
        assert isinstance(static.auth, StaticTokenAuth)

        rotating = MagickMind.from_token(
            BASE_URL, _jwt(aud=AUDIENCE_SUPERVISED), refresh=True
        )
        assert isinstance(rotating.auth, EndUserTokenAuth)
        assert "EndUserTokenAuth" in repr(rotating)

    def test_expires_in_is_passed_through(self):
        client = MagickMind.from_token(BASE_URL, "jwt-abc", expires_in=600)
        assert client.end_user_auth is not None
        assert client.end_user_auth.expires_at is not None

    async def test_provider_errors_are_not_given_route_hints(
        self, httpx_mock: HTTPXMock
    ):
        """A dead credential must surface as what it is, not as a 401 from the
        route the caller happened to be using."""
        httpx_mock.add_response(url=REFRESH_URL, method="POST", status_code=401)
        client = MagickMind.from_token(BASE_URL, _jwt(exp=time.time() + 10))

        with pytest.raises(TokenExpiredError) as exc:
            await client.v1.magickspaces.list_own()

        assert exc.value.hint is None
        assert "hint:" not in str(exc.value)
        await client.close()

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
