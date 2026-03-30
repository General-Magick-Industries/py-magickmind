"""Tests for EventContext and context-aware handler dispatch."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from magick_mind.realtime.events import EventContext
from magick_mind.realtime.handler import EventRouter, _wants_context


# ---------------------------------------------------------------------------
# EventContext.from_channel
# ---------------------------------------------------------------------------


class TestEventContextFromChannel:
    def test_standard_channel(self):
        ctx = EventContext.from_channel("personal:user-42#svc-1")
        assert ctx.target_user_id == "user-42"
        assert ctx.channel == "personal:user-42#svc-1"

    def test_uuid_ids(self):
        ch = "personal:a1b2c3d4-e5f6-7890-abcd-ef1234567890#svc-xyz-999"
        ctx = EventContext.from_channel(ch)
        assert ctx.target_user_id == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert ctx.channel == ch

    def test_empty_string(self):
        ctx = EventContext.from_channel("")
        assert ctx.target_user_id == ""
        assert ctx.channel == ""

    def test_malformed_channel(self):
        ctx = EventContext.from_channel("garbage")
        assert ctx.target_user_id == ""
        assert ctx.channel == "garbage"

    def test_missing_hash(self):
        ctx = EventContext.from_channel("personal:user-42")
        assert ctx.target_user_id == ""

    def test_frozen(self):
        ctx = EventContext.from_channel("personal:u#s")
        with pytest.raises(AttributeError):
            ctx.channel = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# _wants_context introspection
# ---------------------------------------------------------------------------


class TestWantsContext:
    def test_single_arg(self):
        async def handler(event):
            pass

        assert _wants_context(handler) is False

    def test_two_args(self):
        async def handler(event, ctx):
            pass

        assert _wants_context(handler) is True

    def test_kwargs_only(self):
        async def handler(event, *, ctx):
            pass

        assert _wants_context(handler) is False

    def test_var_positional(self):
        async def handler(*args):
            pass

        assert _wants_context(handler) is False


# ---------------------------------------------------------------------------
# EventRouter dispatch with context
# ---------------------------------------------------------------------------

_CHAT_DATA = {
    "type": "chat_message",
    "payload": {
        "mindspace_id": "ms-1",
        "message_id": "msg-1",
        "task_id": "t-1",
        "message": "hello",
    },
}


def _make_pub_ctx(data: dict, channel: str = ""):
    """Build a minimal ServerPublicationContext-like object."""
    pub = MagicMock()
    pub.data = data
    ctx = MagicMock(spec=[])
    ctx.pub = pub
    ctx.channel = channel
    return ctx


@pytest.mark.asyncio
async def test_handler_receives_event_only():
    """Handlers with 1 param still work — backward compat."""
    received: list = []

    router = EventRouter()

    @router.on("chat_message")
    async def handle(event):
        received.append(event)

    await router.on_publication(_make_pub_ctx(_CHAT_DATA, "personal:u1#svc"))
    assert len(received) == 1
    assert received[0].payload.message == "hello"


@pytest.mark.asyncio
async def test_handler_receives_event_and_context():
    """Handlers with 2 params get EventContext as second arg."""
    received: list = []

    router = EventRouter()

    @router.on("chat_message")
    async def handle(event, ctx):
        received.append((event, ctx))

    await router.on_publication(_make_pub_ctx(_CHAT_DATA, "personal:u1#svc"))
    assert len(received) == 1
    event, ctx = received[0]
    assert event.payload.message == "hello"
    assert isinstance(ctx, EventContext)
    assert ctx.target_user_id == "u1"
    assert ctx.channel == "personal:u1#svc"


@pytest.mark.asyncio
async def test_unknown_handler_receives_context():
    received: list = []

    router = EventRouter()

    @router.on_unknown
    async def handle(event, ctx):
        received.append((event, ctx))

    data = {"type": "some_new_type", "payload": {"x": 1}}
    await router.on_publication(_make_pub_ctx(data, "personal:u2#svc"))

    assert len(received) == 1
    event, ctx = received[0]
    assert event.type == "some_new_type"
    assert ctx.target_user_id == "u2"


@pytest.mark.asyncio
async def test_unknown_handler_without_context():
    received: list = []

    router = EventRouter()

    @router.on_unknown
    async def handle(event):
        received.append(event)

    data = {"type": "some_new_type", "payload": {"x": 1}}
    await router.on_publication(_make_pub_ctx(data, "personal:u2#svc"))

    assert len(received) == 1
    assert received[0].type == "some_new_type"


@pytest.mark.asyncio
async def test_context_from_publication_adapter():
    """Simulate the _DelegatingSubscriptionHandler → EventRouter path
    by constructing a _PublicationAdapter directly."""
    from magick_mind.realtime.client import _PublicationAdapter

    received_ctx: list[EventContext] = []

    router = EventRouter()

    @router.on("chat_message")
    async def handle(event, ctx: EventContext):
        received_ctx.append(ctx)

    pub = MagicMock()
    pub.data = _CHAT_DATA
    client_ctx = MagicMock()
    client_ctx.pub = pub

    adapter = _PublicationAdapter(client_ctx, "personal:user-42#svc-1")
    await router.on_publication(adapter)  # type: ignore[arg-type]

    assert len(received_ctx) == 1
    assert received_ctx[0].target_user_id == "user-42"
    assert received_ctx[0].channel == "personal:user-42#svc-1"


@pytest.mark.asyncio
async def test_subscribe_many_different_users_dispatch():
    """Verify different channels produce distinct EventContext per publication."""
    results: dict[str, str] = {}

    router = EventRouter()

    @router.on("chat_message")
    async def handle(event, ctx: EventContext):
        results[ctx.target_user_id] = event.payload.message

    for uid in ("alice", "bob", "carol"):
        data = {
            "type": "chat_message",
            "payload": {
                "mindspace_id": "ms-1",
                "message_id": f"msg-{uid}",
                "task_id": "t-1",
                "message": f"hi {uid}",
            },
        }
        await router.on_publication(_make_pub_ctx(data, f"personal:{uid}#svc-1"))

    assert results == {"alice": "hi alice", "bob": "hi bob", "carol": "hi carol"}
