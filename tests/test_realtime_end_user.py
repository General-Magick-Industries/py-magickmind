"""Realtime as an end user: fan-out parsing, routing, and the connect frame."""

from __future__ import annotations

import base64
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from centrifuge import DisconnectedContext
from pytest_httpx import HTTPXMock

from magick_mind import MagickMind
from magick_mind.auth import EndUserTokenAuth, StaticTokenAuth
from magick_mind.exceptions import MagickMindError
from magick_mind.realtime.client import DISCONNECT_UNAUTHORIZED, RealtimeClient
from magick_mind.realtime.events import (
    MAGICKSPACE_MESSAGE,
    ChatMessageEvent,
    EventContext,
    MagickspaceMessageEvent,
    dispatch_key,
    parse_ws_event,
)
from magick_mind.realtime.handler import EventRouter

BASE_URL = "https://api.test"
WS_URL = "wss://rt.test/connection/websocket"

FANOUT = {
    "type": "chat_message",
    "payload": {
        "id": "msg-1",
        "magickspace_id": "ms-1",
        "sent_by_user_id": "human-1",
        "sent_by_user_name": "Sam",
        "magickspace_type": "GROUP",
        "content": "hi Aria",
        "status": "SENT",
        "message_type": "TEXT",
        "artifact_ids": None,
        "tools": [{"name": "peek", "description": "look", "schema": {}}],
        "context": {"topic": "weather"},
    },
}

XAVIER = {
    "type": "chat_message",
    "payload": {
        "mindspace_id": "ms-1",
        "message_id": "m-1",
        "task_id": "t-1",
        "message": "reply",
    },
}


def _jwt(sub: str, exp: float | None = None) -> str:
    def seg(d: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()

    claims: dict = {"sub": sub}
    if exp is not None:
        claims["exp"] = int(exp)
    return f"{seg({'alg': 'HS256'})}.{seg(claims)}.sig"


class TestEventParsing:
    def test_fanout_parses_as_magickspace_message(self):
        event = parse_ws_event(FANOUT)

        assert isinstance(event, MagickspaceMessageEvent)
        assert event.type == "chat_message"
        assert dispatch_key(event) == MAGICKSPACE_MESSAGE
        assert event.payload.sent_by_user_name == "Sam"
        assert event.payload.magickspace_type == "GROUP"
        assert event.payload.artifact_ids == []
        assert event.payload.tools == [
            {"name": "peek", "description": "look", "schema": {}}
        ]
        assert event.payload.context == {"topic": "weather"}
        assert not event.payload.is_signal and not event.payload.is_control

    def test_xavier_chat_message_still_parses(self):
        event = parse_ws_event(XAVIER)
        assert isinstance(event, ChatMessageEvent)
        assert dispatch_key(event) == "chat_message"

    @pytest.mark.parametrize(
        ("message_type", "signal", "control"),
        [
            ("SIGNAL_START", True, False),
            ("TOOL_MANIFEST", False, True),
            ("TEXT", False, False),
        ],
    )
    def test_signal_and_control_flags(
        self, message_type: str, signal: bool, control: bool
    ):
        payload = {**FANOUT["payload"], "message_type": message_type, "content": ""}
        event = parse_ws_event({"type": "chat_message", "payload": payload})
        assert isinstance(event, MagickspaceMessageEvent)
        assert event.payload.is_signal is signal
        assert event.payload.is_control is control

    def test_event_context_parses_user_channel(self):
        ctx = EventContext.from_channel("user:agent-1#agent-1")
        assert ctx.target_user_id == "agent-1"
        assert EventContext.from_channel("personal:u-1#t-1").target_user_id == "u-1"
        assert EventContext.from_channel("weird").target_user_id == ""


class TestRouting:
    async def test_router_dispatches_fanout_under_its_own_key(self):
        router = EventRouter()
        seen: list[tuple[MagickspaceMessageEvent, EventContext]] = []
        legacy: list[ChatMessageEvent] = []

        @router.on(MAGICKSPACE_MESSAGE)
        async def on_turn(event: MagickspaceMessageEvent, ctx: EventContext) -> None:
            seen.append((event, ctx))

        @router.on("chat_message")
        async def on_chat(event: ChatMessageEvent) -> None:
            legacy.append(event)

        pub = MagicMock()
        pub.data = FANOUT
        await router.on_publication(MagicMock(pub=pub, channel="user:agent-1#agent-1"))
        pub.data = XAVIER
        await router.on_publication(MagicMock(pub=pub, channel="personal:u-1#t-1"))

        assert len(seen) == 1 and len(legacy) == 1
        event, ctx = seen[0]
        assert event.payload.content == "hi Aria"
        assert ctx.target_user_id == "agent-1"


class TestEndUserConnection:
    async def test_connect_puts_token_in_connect_data(self):
        rt = RealtimeClient(StaticTokenAuth("jwt-agent"), WS_URL, end_user=True)

        with patch("magick_mind.realtime.client.Client") as MockClient:
            MockClient.return_value = AsyncMock()
            await rt.connect()

        _, kwargs = MockClient.call_args
        assert kwargs["data"] == {"token": "jwt-agent"}
        assert "get_token" not in kwargs

    async def test_service_user_connect_is_unchanged(self):
        rt = RealtimeClient(StaticTokenAuth("jwt-tenant"), WS_URL)

        with patch("magick_mind.realtime.client.Client") as MockClient:
            MockClient.return_value = AsyncMock()
            await rt.connect()

        _, kwargs = MockClient.call_args
        assert callable(kwargs["get_token"])
        assert "data" not in kwargs

    async def test_rotation_refreshes_the_connect_frame(self, httpx_mock: HTTPXMock):
        """The rotated-out token is revoked, so a reconnect must carry the new one."""
        old = _jwt("agent-1", exp=time.time() + 10)
        new = _jwt("agent-1", exp=time.time() + 3600)
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/end-user/tokens/refresh",
            method="POST",
            json={
                "token": new,
                "expires_at": "x",
                "token_type": "Bearer",
                "expires_in": 3600,
            },
        )
        auth = EndUserTokenAuth(old, BASE_URL)
        rt = RealtimeClient(auth, WS_URL, end_user=True)

        with patch("magick_mind.realtime.client.Client") as MockClient:
            MockClient.return_value = AsyncMock()
            await rt.connect()
        _, kwargs = MockClient.call_args
        connect_data = kwargs["data"]
        assert connect_data == {"token": new}, (
            "connect already rotated the near-expiry token"
        )

        auth.replace_token("jwt-replaced")
        assert connect_data == {"token": "jwt-replaced"}, (
            "the same dict is updated in place"
        )

    async def test_subscribe_is_refused_in_end_user_mode(self):
        rt = RealtimeClient(StaticTokenAuth("jwt-agent"), WS_URL, end_user=True)
        rt._client = MagicMock()

        with pytest.raises(MagickMindError, match="nothing to subscribe"):
            await rt.subscribe("someone")

    async def test_unauthorized_disconnect_is_terminal(self):
        rt = RealtimeClient(StaticTokenAuth("jwt-agent"), WS_URL, end_user=True)

        await rt._router.on_disconnected(
            DisconnectedContext(code=DISCONNECT_UNAUTHORIZED, reason="unauthorized")
        )

        assert rt.terminally_disconnected
        assert rt.last_disconnect is not None and rt.last_disconnect.code == 4501

    def test_from_token_wires_end_user_realtime(self):
        client = MagickMind.from_token(BASE_URL, "jwt-agent", ws_endpoint=WS_URL)
        assert client.realtime.end_user is True
        assert client.realtime.ws_url == WS_URL
