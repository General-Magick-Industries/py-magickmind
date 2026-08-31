# Building an agent process on the SDK

This SDK is a client, not a runtime: it gives an agent process every Bifrost
call it needs and leaves the loop -- what to say, when, with which model --
to you. This guide walks the surface an agent uses, in the order it uses it.

Two credentials appear throughout:

| Credential | Who holds it | Methods |
|---|---|---|
| service-user JWT (`MagickMind(email=, password=)`) | your backend / control plane | everything, including creating agents and minting their tokens |
| end-user JWT (`MagickMind.from_token(token)`) | the agent process | the `*_own` methods, where the caller is the token subject |

The end-user routes carry no `agent_id`, `sender_id` or `participant_id`:
the server takes the identity from the token, so an agent cannot act as
another.

## 1. Create the agent and mint its credential (service user)

```python
from magick_mind import MagickMind

admin = MagickMind(base_url=BASE_URL, email=EMAIL, password=PASSWORD)

agent = await admin.v1.end_user.create(name="Aria", participant_type="AGENT")
await admin.v1.end_user.attach_persona(agent.id, persona_id="p-1", version_id="pv-1")
await admin.v1.magickspaces.add_participants("ms-1", participant_ids=[agent.id])

minted = await admin.v1.end_user.mint_token(agent.id, ttl_seconds=3600)
```

Pass `supervised=True` if your control plane will rotate the token itself.
A supervised token is barred from the self-refresh route, so the agent must
then be built with `refresh=False` (the default) and given replacements out
of band.

## 2. Build the agent client

```python
aria = MagickMind.from_token(
    BASE_URL, minted.token, ws_endpoint=WS_URL, refresh=True
)
```

With `refresh=True` the client holds an `EndUserTokenAuth` that rotates the
token before it expires. Rotation revokes the token it replaces, so never
copy the token elsewhere; ask `await aria.auth.get_token_async()` when you
need the current one.

Rotation happens lazily on each request. An agent that only listens on the
websocket never makes one, so run the rotation loop alongside it:

```python
import asyncio

stop = asyncio.Event()
asyncio.create_task(aria.auth.keep_fresh(stop))   # type: ignore[union-attr]
```

`aria.auth.is_terminal` turns true if the server rejects the credential
outright (`401`/`403` on refresh). Nothing recovers from that except a new
token, delivered with `aria.auth.replace_token(new_token)`.

## 3. Prepare the prompt and the context

```python
persona = await aria.v1.persona.prepare_for_own_agent()
system_prompt = persona.system_prompt            # final; do not assemble

ctx = await aria.v1.magickspaces.prepare_own_context(
    "ms-1", catalog_corpus_ids=granted_corpus_ids
)
history = ctx.chat_history                       # ChatHistoryItem, oldest first
corpora = {c.id: c for c in ctx.corpora}         # what query_own may reach
```

`ctx.corpora` is the catalog of knowledge bases this space can draw from
(the space's own plus any `catalog_corpus_ids` you passed). Tell the model
their ids and descriptions, and validate any id the model hands back by
exact match against this dict before querying.

## 4. Receive turns

Connect as the end user; the server subscribes the connection to the
agent's own `user:` channel, so there is nothing to `subscribe()` to.

```python
from magick_mind import MAGICKSPACE_MESSAGE, MagickspaceMessageEvent

@aria.realtime.on(MAGICKSPACE_MESSAGE)
async def on_turn(event: MagickspaceMessageEvent) -> None:
    turn = event.payload
    if turn.sent_by_user_id == agent.id:          # own echo
        return
    if turn.is_signal or turn.is_control:         # indicators / tool protocol
        return
    await respond(turn)

await aria.realtime.connect()
```

The payload is the stored message plus two wire-only extras: `tools`, the
sender's tool manifest for this turn, and `context`, per-turn key/values the
sender wants in your prompt. Neither is persisted, so read them here or not
at all.

If the connection drops with code `4501` the token was rejected;
`aria.realtime.terminally_disconnected` becomes true and the client will not
reconnect until it has a new token.

## 5. Reply, and tell the room you are working

```python
async def respond(turn):
    await aria.v1.magickspaces.send_own_message("ms-1", message_type="SIGNAL_START")
    try:
        text = await think(turn)
        await aria.v1.magickspaces.send_own_message(
            "ms-1", content=text, reply_to_message_id=turn.id
        )
    except Exception:
        await aria.v1.magickspaces.send_own_message("ms-1", message_type="SIGNAL_ERROR")
        raise
    finally:
        await aria.v1.magickspaces.send_own_message("ms-1", message_type="SIGNAL_END")
```

`send_own_message` is the only send that reaches other agents; the
service-user `send_message` publishes to channels agents do not listen on.
Signals are fanned out but never stored, so they cost nothing in history.

## 6. Remember

Ingest both sides of the conversation, best-effort -- a memory outage should
not stop the reply:

```python
async def remember(turn, reply_text, reply_id):
    for sender, text, mid in ((turn.sent_by_user_id, turn.content, turn.id),
                              (agent.id, reply_text, reply_id)):
        try:
            await aria.v1.episode.process_own(
                magickspace_id="ms-1", sender_id=sender, message=text,
                message_id=mid, client_message_id=mid, is_group=True,
            )
        except Exception:
            log.warning("episodic ingest failed", exc_info=True)
```

Recall answers two different questions:

```python
what = await aria.v1.episode.search_own("the trip to Paris", magickspace_id="ms-1")
when = await aria.v1.episode.list_range_own(date_start="2026-08-01", date_end="2026-08-31")
```

`search_own` ranks by relevance and returns prompt-ready text in
`memory_content`; `list_range_own` returns `Episode` objects in an inclusive
date window, newest first, and is the one to use for "what happened last
week".

## 7. Knowledge and files

```python
hit = await aria.v1.corpus.query_own(corpus_id, query=q, api_key=LITELLM_KEY)

presigned = await aria.v1.artifact.presign_own_upload(
    "ms-1", content_type="image/png", size_bytes=len(png)
)
httpx.put(presigned.upload_url, content=png, headers=presigned.required_headers)
await aria.v1.artifact.finalize_own(
    "ms-1", artifact_id=presigned.id, bucket=presigned.bucket, key=presigned.key
)
await aria.v1.magickspaces.send_own_message("ms-1", artifact_ids=[presigned.id])
```

Artifacts attached to messages in a space are reachable while the agent is
a participant (`get_own`, `download_url_own`); the ones it uploaded itself
stay reachable afterwards (`get_owned`, `download_url_owned`).
