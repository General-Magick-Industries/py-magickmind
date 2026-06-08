"""API-key client for the Cortex v2 Reason HTTP/SSE endpoint."""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Literal, Mapping, overload

import httpx

from magick_mind.exceptions import MagickMindError
from magick_mind.reasoning.events import ReasonEvent, iter_sse_events
from magick_mind.reasoning.models import ChatMessage, ReasonResponse


DEFAULT_BASE_URL = "https://api.magickmind.ai"
REASON_PATH = "/v2/cortex/chat/completions"


class ReasonStream:
    """Async iterator over typed Reason stream events."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> None:
        self._client = client
        self._url = url
        self._headers = headers
        self._payload = payload

    def __aiter__(self) -> AsyncIterator[ReasonEvent]:
        return self._iter_events()

    async def _iter_events(self) -> AsyncIterator[ReasonEvent]:
        async with self._client.stream(
            "POST",
            self._url,
            json=self._payload,
            headers=self._headers,
        ) as response:
            await _raise_for_error(response)
            async for event in iter_sse_events(response.aiter_lines()):
                yield event


class Client:
    """Typed Python SDK client for Cortex v2 Reason."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float | httpx.Timeout = 30.0,
        max_retries: int = 2,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max(0, max_retries)
        self._owns_http_client = http_client is None
        self._client = http_client or httpx.AsyncClient(timeout=timeout)

    @overload
    async def reason(
        self,
        *,
        algorithm: Any,
        messages: list[Mapping[str, Any] | ChatMessage] | None = None,
        message: str | None = None,
        stream: Literal[False] = False,
        trace_id: str | None = None,
        response_format: str | None = None,
        verified: bool | None = None,
        message_id: str | None = None,
        user_id: str | None = None,
    ) -> ReasonResponse: ...

    @overload
    async def reason(
        self,
        *,
        algorithm: Any,
        messages: list[Mapping[str, Any] | ChatMessage] | None = None,
        message: str | None = None,
        stream: Literal[True],
        trace_id: str | None = None,
        response_format: str | None = None,
        verified: bool | None = None,
        message_id: str | None = None,
        user_id: str | None = None,
    ) -> ReasonStream: ...

    async def reason(
        self,
        *,
        algorithm: Any,
        messages: list[Mapping[str, Any] | ChatMessage] | None = None,
        message: str | None = None,
        stream: bool = False,
        trace_id: str | None = None,
        response_format: str | None = None,
        verified: bool | None = None,
        message_id: str | None = None,
        user_id: str | None = None,
    ) -> ReasonResponse | ReasonStream:
        """Call Cortex v2 Reason.

        Pass either ``messages`` or ``message``. When ``stream=True``, the return
        value is an async iterator of typed ``ReasonEvent`` objects.
        """
        payload = self._build_reason_payload(
            algorithm=algorithm,
            messages=messages,
            message=message,
            stream=stream,
            trace_id=trace_id,
            response_format=response_format,
            verified=verified,
            message_id=message_id,
            user_id=user_id,
        )
        headers = self._headers(stream=stream)
        url = f"{self.base_url}{REASON_PATH}"

        if stream:
            return ReasonStream(self._client, url, headers, payload)

        response = await self._post_json_with_retries(url, payload, headers)
        return ReasonResponse.model_validate(response.json())

    def _build_reason_payload(
        self,
        *,
        algorithm: Any,
        messages: list[Mapping[str, Any] | ChatMessage] | None,
        message: str | None,
        stream: bool,
        trace_id: str | None,
        response_format: str | None,
        verified: bool | None,
        message_id: str | None,
        user_id: str | None,
    ) -> dict[str, Any]:
        if messages is None and message is None:
            raise ValueError("messages or message is required")
        if messages is not None and message is not None:
            raise ValueError("pass either messages or message, not both")

        input_payload: dict[str, Any]
        if messages is not None:
            input_payload = {"messages": [_message_to_dict(item) for item in messages]}
        else:
            input_payload = {"message": message}

        payload = {
            "input": input_payload,
            "algorithm": _to_wire_dict(algorithm),
            "stream": stream,
            "trace_id": trace_id,
            "response_format": response_format,
            "verified": verified,
            "message_id": message_id,
            "user_id": user_id,
        }
        return {key: value for key, value in payload.items() if value is not None}

    def _headers(self, *, stream: bool) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if stream else "application/json",
        }

    async def _post_json_with_retries(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.post(url, json=payload, headers=headers)
                if response.status_code not in _RETRYABLE_STATUS_CODES:
                    await _raise_for_error(response)
                    return response
                await _raise_for_error(response)
            except (httpx.TimeoutException, httpx.NetworkError, MagickMindError) as exc:
                last_error = exc
                if attempt >= self.max_retries or not _is_retryable_exception(exc):
                    raise
                await asyncio.sleep(0.25 * (2**attempt))

        if last_error:
            raise last_error
        raise MagickMindError("Reason request failed before receiving a response")

    async def close(self) -> None:
        if self._owns_http_client:
            await self._client.aclose()

    async def __aenter__(self) -> Client:
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc_val: object,
        exc_tb: object,
    ) -> None:
        await self.close()


_RETRYABLE_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}


def _to_wire_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        data = value.to_dict()
    elif isinstance(value, Mapping):
        data = dict(value)
    else:
        raise TypeError("algorithm must be a mapping or expose to_dict()")
    return data


def _message_to_dict(value: Mapping[str, Any] | ChatMessage) -> dict[str, Any]:
    if isinstance(value, ChatMessage):
        return value.model_dump()
    return dict(value)


async def _raise_for_error(response: httpx.Response) -> None:
    if response.status_code < 400:
        return

    detail = response.text
    try:
        data = response.json()
    except ValueError:
        data = None
    if isinstance(data, dict):
        if "error" in data and isinstance(data["error"], dict):
            detail = str(data["error"].get("detail") or data["error"].get("title"))
        elif "message" in data:
            detail = str(data["message"])
    raise MagickMindError(detail, status_code=response.status_code)


def _is_retryable_exception(exc: Exception) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)):
        return True
    return isinstance(exc, MagickMindError) and exc.status_code in _RETRYABLE_STATUS_CODES
