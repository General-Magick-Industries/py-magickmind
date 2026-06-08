from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock, IteratorStream

from magickmind import (
    AlgorithmConfig,
    Client,
    LLM,
    MCTS,
    ModelConfig,
    NodeConfig,
    RLM,
    ReasonResponse,
    Singular,
)
from magick_mind.reasoning.events import (
    ReasonCompleteEvent,
    ReasonThinkingEvent,
    ReasonTokenEvent,
    parse_sse_text,
)


async def test_reason_non_streaming_posts_wire_payload(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.test/v2/cortex/chat/completions",
        json={
            "text_answer": "hello from cortex",
            "trace_id": "trace-1",
            "success": True,
            "usage": {"input_tokens": 3, "output_tokens": 4, "llm_calls": 1},
        },
    )

    client = Client(api_key="sk-test", base_url="https://api.test")
    result = await client.reason(
        algorithm=Singular(LLM("openrouter/openai/gpt-4o")),
        messages=[{"role": "user", "content": "hello"}],
        trace_id="trace-1",
    )

    assert isinstance(result, ReasonResponse)
    assert result.content == "hello from cortex"
    assert result.usage is not None
    assert result.usage.llm_calls == 1

    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["Authorization"] == "Bearer sk-test"
    assert request.headers["Accept"] == "application/json"
    assert request.read() == (
        b'{"input":{"messages":[{"role":"user","content":"hello"}]},'
        b'"algorithm":{"singular":{"node":{"llm":{"model_config":'
        b'{"model":"openrouter/openai/gpt-4o"}}}}},"stream":false,'
        b'"trace_id":"trace-1"}'
    )

    await client.close()


async def test_reason_streaming_yields_typed_events(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.test/v2/cortex/chat/completions",
        headers={"Content-Type": "text/event-stream"},
        stream=IteratorStream(
            [
                b'event: reason.started\ndata: {"trace_id":"trace-1","started":{"algorithm":"singular"}}\n\n',
                b'event: reason.answer.delta\ndata: {"trace_id":"trace-1","answer_chunk":{"content":"hel"}}\n\n',
                b'event: reason.answer.delta\ndata: {"trace_id":"trace-1","answer_chunk":{"content":"lo"}}\n\n',
                b'event: reason.answer.complete\ndata: {"trace_id":"trace-1","answer_complete":{}}\n\n',
            ]
        ),
    )

    client = Client(api_key="sk-test", base_url="https://api.test")
    result = await client.reason(
        algorithm={"singular": {"node": {"llm": {"model": "legacy-model"}}}},
        message="hello",
        stream=True,
    )

    events = [event async for event in result]

    assert isinstance(events[0], ReasonThinkingEvent)
    assert events[0].is_thinking()
    assert isinstance(events[1], ReasonTokenEvent)
    assert events[1].is_token()
    assert events[1].content == "hel"
    assert events[2].content == "lo"
    assert isinstance(events[3], ReasonCompleteEvent)

    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["Authorization"] == "Bearer sk-test"
    assert request.headers["Accept"] == "text/event-stream"

    await client.close()


def test_parse_sse_text_handles_reason_taxonomy() -> None:
    events = parse_sse_text(
        'event: reason.rlm.repl_step\ndata: {"trace_id":"t","rlm_repl_step":{"iteration":1,"reasoning":"try code"}}\n\n'
        'event: reason.answer.delta\ndata: {"trace_id":"t","answer_chunk":{"content":"x"}}\n\n'
    )

    assert events[0].is_thinking()
    assert events[0].payload["reasoning"] == "try code"
    assert events[1].is_token()
    assert events[1].content == "x"


def test_mcts_builder_matches_v2_wire_format() -> None:
    body = MCTS(
        nodes=[
            LLM("openrouter/anthropic/claude-sonnet-4"),
            LLM("openrouter/openai/gpt-4o"),
        ],
        iterations=4,
        rating_model="openrouter/openai/gpt-4o-mini",
        aggregator_model="openrouter/openai/gpt-4o",
    ).to_dict()

    assert body == {
        "mcts": {
            "nodes": [
                {
                    "llm": {
                        "model_config": {
                            "model": "openrouter/anthropic/claude-sonnet-4"
                        }
                    }
                },
                {"llm": {"model_config": {"model": "openrouter/openai/gpt-4o"}}},
            ],
            "iterations": 4,
            "rating_model_config": {"model": "openrouter/openai/gpt-4o-mini"},
            "aggregator_model_config": {"model": "openrouter/openai/gpt-4o"},
        }
    }


def test_llm_builder_supports_inline_model_config() -> None:
    body = LLM(
        "provider/model",
        temperature=0.2,
        max_tokens=256,
        top_p=0.9,
        reasoning_effort="medium",
    ).to_dict()

    assert body == {
        "llm": {
            "model_config": {
                "model": "provider/model",
                "temperature": 0.2,
                "max_tokens": 256,
                "top_p": 0.9,
                "reasoning_effort": "medium",
            }
        }
    }


def test_llm_builder_accepts_model_config() -> None:
    body = LLM(ModelConfig(model="provider/model", max_tokens=128)).to_dict()

    assert body == {
        "llm": {
            "model_config": {
                "model": "provider/model",
                "max_tokens": 128,
            }
        }
    }


def test_llm_builder_rejects_model_config_with_inline_overrides() -> None:
    with pytest.raises(ValueError, match="cannot be passed alongside ModelConfig"):
        LLM(ModelConfig(model="provider/model"), temperature=0.2)


def test_mcts_builder_defaults_iterations_to_four() -> None:
    body = MCTS(
        nodes=[LLM("provider/model-a"), LLM("provider/model-b")],
        rating_model="provider/rating-model",
        aggregator_model="provider/aggregator-model",
    ).to_dict()

    assert body["mcts"]["iterations"] == 4


def test_rlm_builder_matches_current_v2_wire_format() -> None:
    body = RLM(
        decomposer_model="openrouter/openai/gpt-4o",
        leaf_model="openrouter/openai/gpt-4o-mini",
        max_depth=2,
    ).to_dict()

    assert body == {
        "rlm": {
            "main_model_config": {"model": "openrouter/openai/gpt-4o"},
            "sub_model_config": {"model": "openrouter/openai/gpt-4o-mini"},
            "max_iterations": 2,
        }
    }


def test_builder_type_aliases_are_usable_for_annotations() -> None:
    node: NodeConfig = LLM("provider/model")
    algorithm: AlgorithmConfig = Singular(node)

    assert isinstance(algorithm, Singular)
    assert algorithm.to_dict() == {
        "singular": {
            "node": {
                "llm": {
                    "model_config": {
                        "model": "provider/model",
                    }
                }
            }
        }
    }


def test_rlm_builder_rejects_unsupported_draft_fields() -> None:
    with pytest.raises(ValueError, match="synthesizer_model, fanout"):
        RLM(
            decomposer_model="openrouter/openai/gpt-4o",
            leaf_model="openrouter/openai/gpt-4o-mini",
            synthesizer_model="openrouter/openai/gpt-4o",
            fanout=3,
        )


async def test_reason_raises_api_errors(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.test/v2/cortex/chat/completions",
        status_code=401,
        json={"code": 401, "message": "Unauthorized access"},
    )
    client = Client(api_key="sk-test", base_url="https://api.test", max_retries=0)

    with pytest.raises(Exception, match="Unauthorized access"):
        await client.reason(
            algorithm=Singular(LLM("openrouter/openai/gpt-4o")),
            message="hello",
        )

    await client.close()
