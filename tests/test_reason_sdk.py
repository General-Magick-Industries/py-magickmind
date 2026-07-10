from __future__ import annotations

import json

import httpx
import pytest
from pytest_httpx import HTTPXMock, IteratorStream

from magickmind import (
    AlgorithmConfig,
    Client,
    ImageSize,
    Lambda,
    LLM,
    MCTS,
    ModelConfig,
    NodeConfig,
    RLM,
    ReasonResponse,
    Singular,
)
from magick_mind import MagickMind
from magick_mind.resources.v2.events import (
    ReasonCompleteEvent,
    ReasonThinkingEvent,
    ReasonTokenEvent,
    parse_sse_text,
)


async def test_v2_reason_resource_posts_with_api_key(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.test/v2/chat/completions",
        json={"text_answer": "hello from resource", "success": True},
    )

    client = MagickMind(
        base_url="https://api.test",
        email="test@example.com",
        password="secret",
    )
    result = await client.v2.reason(
        api_key="sk-test",
        algorithm=Singular(LLM("openrouter/openai/gpt-4o")),
        message="hello",
    )

    assert result.content == "hello from resource"
    assert client.reason is client.v2.reason

    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["Authorization"] == "Bearer sk-test"
    assert request.headers["Accept"] == "application/json"

    await client.close()


async def test_v2_reason_resource_can_use_shared_auth(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.test/v1/auth/login",
        json={
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 3600,
            "refresh_expires_in": 86400,
            "token_type": "Bearer",
            "id_token": "test-id-token",
            "not-before-policy": 0,
            "session_state": "test-session-state",
            "scope": "openid profile email",
        },
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.test/v2/chat/completions",
        json={"text_answer": "hello with jwt", "success": True},
    )

    client = MagickMind(
        base_url="https://api.test",
        email="test@example.com",
        password="secret",
    )
    result = await client.reason(
        algorithm=Singular(LLM("openrouter/openai/gpt-4o")),
        message="hello",
    )

    assert result.content == "hello with jwt"
    reason_request = httpx_mock.get_requests()[-1]
    assert reason_request.headers["Authorization"] == "Bearer test-access-token"

    await client.close()


async def test_reason_non_streaming_posts_wire_payload(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.test/v2/chat/completions",
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
    assert json.loads(request.read()) == {
        "messages": [{"role": "user", "content": "hello"}],
        "algorithm": {
            "singular": {
                "node": {
                    "llm": {
                        "model_config": {
                            "model": "openrouter/openai/gpt-4o",
                        }
                    }
                }
            }
        },
        "stream": False,
        "trace_id": "trace-1",
    }

    await client.close()


async def test_reason_message_only_builds_openai_messages(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.test/v2/chat/completions",
        json={"text_answer": "hello from cortex", "success": True},
    )

    client = Client(api_key="sk-test", base_url="https://api.test")
    await client.reason(model="gpt-5.1", message="hello", temperature=0.7)

    request = httpx_mock.get_request()
    assert request is not None
    assert json.loads(request.read()) == {
        "model": "gpt-5.1",
        "message": "hello",
        "messages": [{"role": "user", "content": "hello"}],
        "stream": False,
        "temperature": 0.7,
    }

    await client.close()


async def test_reason_allows_message_override_with_messages(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.test/v2/chat/completions",
        json={"text_answer": "hello from cortex", "success": True},
    )

    client = Client(api_key="sk-test", base_url="https://api.test")
    await client.reason(
        model="gpt-5.1",
        message="legacy prompt",
        messages=[
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "openai prompt"},
        ],
        max_tokens=1000,
        top_p=0.9,
    )

    request = httpx_mock.get_request()
    assert request is not None
    assert json.loads(request.read()) == {
        "model": "gpt-5.1",
        "message": "legacy prompt",
        "messages": [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "openai prompt"},
        ],
        "stream": False,
        "max_tokens": 1000,
        "top_p": 0.9,
    }

    await client.close()


async def test_reason_streaming_yields_typed_events(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.test/v2/chat/completions",
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


async def test_reason_streaming_retries_before_first_event(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_exception(
        httpx.ReadTimeout("stream connect timed out"),
        method="POST",
        url="https://api.test/v2/chat/completions",
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.test/v2/chat/completions",
        headers={"Content-Type": "text/event-stream"},
        stream=IteratorStream(
            [
                b'event: reason.answer.delta\ndata: {"trace_id":"trace-1","answer_chunk":{"content":"ok"}}\n\n',
            ]
        ),
    )

    client = Client(api_key="sk-test", base_url="https://api.test", max_retries=1)
    result = await client.reason(
        algorithm=Singular(LLM("openrouter/openai/gpt-4o")),
        message="hello",
        stream=True,
    )

    events = [event async for event in result]

    assert len(httpx_mock.get_requests()) == 2
    assert events[0].content == "ok"

    await client.close()


async def test_reason_streaming_retries_retryable_http_status(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.test/v2/chat/completions",
        status_code=503,
        headers={"Content-Type": "application/json"},
        stream=IteratorStream([b'{"message":"temporarily unavailable"}']),
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.test/v2/chat/completions",
        headers={"Content-Type": "text/event-stream"},
        stream=IteratorStream(
            [
                b'event: reason.answer.delta\ndata: {"trace_id":"trace-1","answer_chunk":{"content":"ok"}}\n\n',
            ]
        ),
    )

    client = Client(api_key="sk-test", base_url="https://api.test", max_retries=1)
    result = await client.reason(
        algorithm=Singular(LLM("openrouter/openai/gpt-4o")),
        message="hello",
        stream=True,
    )

    events = [event async for event in result]

    assert len(httpx_mock.get_requests()) == 2
    assert events[0].content == "ok"

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
        main_model_config="openrouter/openai/gpt-4o",
        sub_model_config="openrouter/openai/gpt-4o-mini",
        max_iterations=2,
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


def test_rlm_builder_omits_unset_optional_fields() -> None:
    body = RLM(main_model_config="openrouter/openai/gpt-4o").to_dict()

    assert body == {"rlm": {"main_model_config": {"model": "openrouter/openai/gpt-4o"}}}


def test_lambda_builder_matches_current_v2_wire_format() -> None:
    body = Lambda(
        main_model_config="openrouter/openai/gpt-4o",
        sub_model_config="openrouter/openai/gpt-4o-mini",
        context_window_chars=50000,
        accuracy_target=0.9,
    ).to_dict()

    assert body == {
        "lambda": {
            "main_model_config": {"model": "openrouter/openai/gpt-4o"},
            "sub_model_config": {"model": "openrouter/openai/gpt-4o-mini"},
            "context_window_chars": 50000,
            "accuracy_target": 0.9,
        }
    }


def test_lambda_builder_omits_unset_optional_fields() -> None:
    body = Lambda(main_model_config="openrouter/openai/gpt-4o").to_dict()

    assert body == {
        "lambda": {"main_model_config": {"model": "openrouter/openai/gpt-4o"}}
    }


def test_lambda_builder_accepts_model_config_slots() -> None:
    body = Lambda(
        main_model_config=ModelConfig(
            model="openrouter/openai/gpt-4o", temperature=0.2
        ),
    ).to_dict()

    assert body["lambda"]["main_model_config"] == {
        "model": "openrouter/openai/gpt-4o",
        "temperature": 0.2,
    }


def test_lambda_node_in_singular_algorithm() -> None:
    body = Singular(Lambda(main_model_config="provider/model")).to_dict()

    assert body == {
        "singular": {
            "node": {"lambda": {"main_model_config": {"model": "provider/model"}}}
        }
    }


def test_lambda_node_as_mcts_candidate() -> None:
    body = MCTS(
        nodes=[LLM("provider/model-a"), Lambda(main_model_config="provider/model-b")],
        rating_model="provider/rating-model",
        aggregator_model="provider/aggregator-model",
    ).to_dict()

    assert body["mcts"]["nodes"] == [
        {"llm": {"model_config": {"model": "provider/model-a"}}},
        {"lambda": {"main_model_config": {"model": "provider/model-b"}}},
    ]


def test_rlm_builder_supports_image_model_config() -> None:
    body = RLM(
        main_model_config="openrouter/openai/gpt-4o",
        image_model_config="openrouter/openai/gpt-image-1",
        max_iterations=3,
    ).to_dict()

    assert body == {
        "rlm": {
            "main_model_config": {"model": "openrouter/openai/gpt-4o"},
            "image_model_config": {"model": "openrouter/openai/gpt-image-1"},
            "max_iterations": 3,
        }
    }


def test_model_config_omits_image_config_when_unset() -> None:
    assert ModelConfig(model="provider/model", temperature=0.3).to_dict() == {
        "model": "provider/model",
        "temperature": 0.3,
    }


def test_model_config_serializes_image_size() -> None:
    assert ModelConfig(
        model="openrouter/openai/gpt-image-1",
        image_size=ImageSize.SIZE_1024,
    ).to_dict() == {
        "model": "openrouter/openai/gpt-image-1",
        "image_config": {"size": "IMAGE_SIZE_1024X1024"},
    }


def test_image_model_config_with_size_in_rlm() -> None:
    body = RLM(
        main_model_config="openrouter/openai/gpt-4o",
        image_model_config=ModelConfig(
            model="openrouter/openai/gpt-image-1",
            image_size=ImageSize.SIZE_2048,
        ),
    ).to_dict()

    assert body["rlm"]["image_model_config"] == {
        "model": "openrouter/openai/gpt-image-1",
        "image_config": {"size": "IMAGE_SIZE_2048X2048"},
    }


async def test_reason_raises_api_errors(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.test/v2/chat/completions",
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
