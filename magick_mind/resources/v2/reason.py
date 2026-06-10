"""Resource client for the Cortex v2 Reason HTTP/SSE endpoint."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, AsyncIterator, Literal, Mapping, overload

import httpx

from magick_mind.exceptions import MagickMindError
from magick_mind.models.v2.reason import AlgorithmConfig, ChatMessage, ReasonResponse
from magick_mind.resources.base import BaseResource
from magick_mind.resources.v2.events import ReasonEvent, iter_sse_events

if TYPE_CHECKING:
    from magick_mind.http import HTTPClient


DEFAULT_BASE_URL = "https://api.magickmind.ai"
REASON_PATH = "/v2/chat/completions"


class ReasonStream:
    """Async iterator over typed Reason stream events."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        max_retries: int,
    ) -> None:
        self._client = client
        self._url = url
        self._headers = headers
        self._payload = payload
        self._max_retries = max_retries

    def __aiter__(self) -> AsyncIterator[ReasonEvent]:
        return self._iter_events()

    async def _iter_events(self) -> AsyncIterator[ReasonEvent]:
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            yielded_any = False
            try:
                async with self._client.stream(
                    "POST",
                    self._url,
                    json=self._payload,
                    headers=self._headers,
                ) as response:
                    if response.status_code >= 400:
                        await response.aread()
                    await _raise_for_error(response)
                    async for event in iter_sse_events(response.aiter_lines()):
                        yielded_any = True
                        yield event
                    return
            except (httpx.TimeoutException, httpx.NetworkError, MagickMindError) as exc:
                last_error = exc
                if (
                    yielded_any
                    or attempt >= self._max_retries
                    or not _is_retryable_exception(exc)
                ):
                    raise
                await asyncio.sleep(0.25 * (2**attempt))

        if last_error:
            raise last_error
        raise MagickMindError("Reason stream failed before receiving a response")


class HTTPReasonStream:
    """Async iterator over typed Reason stream events from the shared HTTP client."""

    def __init__(
        self,
        http_client: HTTPClient,
        headers: dict[str, str],
        payload: dict[str, Any],
        max_retries: int,
        use_auth: bool,
    ) -> None:
        self._http = http_client
        self._headers = headers
        self._payload = payload
        self._max_retries = max_retries
        self._use_auth = use_auth

    def __aiter__(self) -> AsyncIterator[ReasonEvent]:
        return self._iter_events()

    async def _iter_events(self) -> AsyncIterator[ReasonEvent]:
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            yielded_any = False
            try:
                async with self._http.stream(
                    "POST",
                    REASON_PATH,
                    json=self._payload,
                    headers=self._headers,
                    use_auth=self._use_auth,
                ) as response:
                    if response.status_code >= 400:
                        await response.aread()
                    await _raise_for_error(response)
                    async for event in iter_sse_events(response.aiter_lines()):
                        yielded_any = True
                        yield event
                    return
            except (httpx.TimeoutException, httpx.NetworkError, MagickMindError) as exc:
                last_error = exc
                if (
                    yielded_any
                    or attempt >= self._max_retries
                    or not _is_retryable_exception(exc)
                ):
                    raise
                await asyncio.sleep(0.25 * (2**attempt))

        if last_error:
            raise last_error
        raise MagickMindError("Reason stream failed before receiving a response")


class ReasonResourceV2(BaseResource):
    """Typed resource for Cortex v2 Reason."""

    def __init__(self, http_client: HTTPClient, max_retries: int = 2) -> None:
        super().__init__(http_client)
        self.max_retries = max(0, max_retries)

    @overload
    async def __call__(
        self,
        *,
        algorithm: AlgorithmConfig | None = None,
        model: str | None = None,
        messages: list[Mapping[str, Any] | ChatMessage] | None = None,
        message: str | None = None,
        stream: Literal[False] = False,
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        trace_id: str | None = None,
        response_format: str | None = None,
        verified: bool | None = None,
        message_id: str | None = None,
        user_id: str | None = None,
        api_key: str | None = None,
    ) -> ReasonResponse: ...

    @overload
    async def __call__(
        self,
        *,
        algorithm: AlgorithmConfig | None = None,
        model: str | None = None,
        messages: list[Mapping[str, Any] | ChatMessage] | None = None,
        message: str | None = None,
        stream: Literal[True],
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        trace_id: str | None = None,
        response_format: str | None = None,
        verified: bool | None = None,
        message_id: str | None = None,
        user_id: str | None = None,
        api_key: str | None = None,
    ) -> HTTPReasonStream: ...

    async def __call__(
        self,
        *,
        algorithm: AlgorithmConfig | None = None,
        model: str | None = None,
        messages: list[Mapping[str, Any] | ChatMessage] | None = None,
        message: str | None = None,
        stream: bool = False,
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        trace_id: str | None = None,
        response_format: str | None = None,
        verified: bool | None = None,
        message_id: str | None = None,
        user_id: str | None = None,
        api_key: str | None = None,
    ) -> ReasonResponse | HTTPReasonStream:
        """Call Cortex v2 Reason using the shared SDK HTTP client."""
        return await self._request(
            algorithm=algorithm,
            model=model,
            messages=messages,
            message=message,
            stream=stream,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            trace_id=trace_id,
            response_format=response_format,
            verified=verified,
            message_id=message_id,
            user_id=user_id,
            api_key=api_key,
        )

    @overload
    async def create(
        self,
        *,
        algorithm: AlgorithmConfig | None = None,
        model: str | None = None,
        messages: list[Mapping[str, Any] | ChatMessage] | None = None,
        message: str | None = None,
        stream: Literal[False] = False,
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        trace_id: str | None = None,
        response_format: str | None = None,
        verified: bool | None = None,
        message_id: str | None = None,
        user_id: str | None = None,
        api_key: str | None = None,
    ) -> ReasonResponse: ...

    @overload
    async def create(
        self,
        *,
        algorithm: AlgorithmConfig | None = None,
        model: str | None = None,
        messages: list[Mapping[str, Any] | ChatMessage] | None = None,
        message: str | None = None,
        stream: Literal[True],
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        trace_id: str | None = None,
        response_format: str | None = None,
        verified: bool | None = None,
        message_id: str | None = None,
        user_id: str | None = None,
        api_key: str | None = None,
    ) -> HTTPReasonStream: ...

    async def create(
        self,
        *,
        algorithm: AlgorithmConfig | None = None,
        model: str | None = None,
        messages: list[Mapping[str, Any] | ChatMessage] | None = None,
        message: str | None = None,
        stream: bool = False,
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        trace_id: str | None = None,
        response_format: str | None = None,
        verified: bool | None = None,
        message_id: str | None = None,
        user_id: str | None = None,
        api_key: str | None = None,
    ) -> ReasonResponse | HTTPReasonStream:
        """Call Cortex v2 Reason."""
        return await self._request(
            algorithm=algorithm,
            model=model,
            messages=messages,
            message=message,
            stream=stream,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            trace_id=trace_id,
            response_format=response_format,
            verified=verified,
            message_id=message_id,
            user_id=user_id,
            api_key=api_key,
        )

    async def _request(
        self,
        *,
        algorithm: AlgorithmConfig | None,
        model: str | None,
        messages: list[Mapping[str, Any] | ChatMessage] | None,
        message: str | None,
        stream: bool,
        temperature: float | None,
        max_tokens: int | None,
        top_p: float | None,
        trace_id: str | None,
        response_format: str | None,
        verified: bool | None,
        message_id: str | None,
        user_id: str | None,
        api_key: str | None,
    ) -> ReasonResponse | HTTPReasonStream:
        payload = _build_reason_payload(
            algorithm=algorithm,
            model=model,
            messages=messages,
            message=message,
            stream=stream,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            trace_id=trace_id,
            response_format=response_format,
            verified=verified,
            message_id=message_id,
            user_id=user_id,
        )
        headers = _headers(stream=stream, api_key=api_key)
        use_auth = api_key is None

        if stream:
            return HTTPReasonStream(
                self._http,
                headers,
                payload,
                self.max_retries,
                use_auth,
            )

        response = await self._post_json_with_retries(payload, headers, use_auth)
        return ReasonResponse.model_validate(response.json())

    async def _post_json_with_retries(
        self,
        payload: dict[str, Any],
        headers: dict[str, str],
        use_auth: bool,
    ) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._http.raw_request(
                    "POST",
                    REASON_PATH,
                    json=payload,
                    headers=headers,
                    use_auth=use_auth,
                )
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


class Client:
    """Standalone API-key client for Cortex v2 Reason.

    Prefer ``MagickMind(...).v2.reason`` for new SDK code.
    """

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
        algorithm: AlgorithmConfig | None = None,
        model: str | None = None,
        messages: list[Mapping[str, Any] | ChatMessage] | None = None,
        message: str | None = None,
        stream: Literal[False] = False,
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
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
        algorithm: AlgorithmConfig | None = None,
        model: str | None = None,
        messages: list[Mapping[str, Any] | ChatMessage] | None = None,
        message: str | None = None,
        stream: Literal[True],
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        trace_id: str | None = None,
        response_format: str | None = None,
        verified: bool | None = None,
        message_id: str | None = None,
        user_id: str | None = None,
    ) -> ReasonStream: ...

    async def reason(
        self,
        *,
        algorithm: AlgorithmConfig | None = None,
        model: str | None = None,
        messages: list[Mapping[str, Any] | ChatMessage] | None = None,
        message: str | None = None,
        stream: bool = False,
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
        trace_id: str | None = None,
        response_format: str | None = None,
        verified: bool | None = None,
        message_id: str | None = None,
        user_id: str | None = None,
    ) -> ReasonResponse | ReasonStream:
        """Call Cortex v2 Reason.

        Pass OpenAI-compatible ``messages`` or the convenience ``message``.
        When ``stream=True``, the return value is an async iterator of typed
        ``ReasonEvent`` objects.
        """
        payload = _build_reason_payload(
            algorithm=algorithm,
            model=model,
            messages=messages,
            message=message,
            stream=stream,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            trace_id=trace_id,
            response_format=response_format,
            verified=verified,
            message_id=message_id,
            user_id=user_id,
        )
        headers = _headers(stream=stream, api_key=self.api_key)
        url = f"{self.base_url}{REASON_PATH}"

        if stream:
            return ReasonStream(
                self._client,
                url,
                headers,
                payload,
                self.max_retries,
            )

        response = await self._post_json_with_retries(url, payload, headers)
        return ReasonResponse.model_validate(response.json())

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


def _build_reason_payload(
    *,
    algorithm: AlgorithmConfig | None,
    model: str | None,
    messages: list[Mapping[str, Any] | ChatMessage] | None,
    message: str | None,
    stream: bool,
    temperature: float | None,
    max_tokens: int | None,
    top_p: float | None,
    trace_id: str | None,
    response_format: str | None,
    verified: bool | None,
    message_id: str | None,
    user_id: str | None,
) -> dict[str, Any]:
    if algorithm is None and not model:
        raise ValueError("model or algorithm is required")
    if messages is None and message is None:
        raise ValueError("messages or message is required")
    if messages is not None and len(messages) == 0:
        raise ValueError("messages must not be empty")

    if messages is None:
        message_items = [{"role": "user", "content": message}]
    else:
        message_items = [_message_to_dict(item) for item in messages]

    payload = {
        "model": model,
        "message": message,
        "messages": message_items,
        "algorithm": _to_wire_dict(algorithm) if algorithm is not None else None,
        "stream": stream,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "trace_id": trace_id,
        "response_format": response_format,
        "verified": verified,
        "message_id": message_id,
        "user_id": user_id,
    }
    return {key: value for key, value in payload.items() if value is not None}


def _headers(*, stream: bool, api_key: str | None = None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream" if stream else "application/json",
    }
    if api_key is not None:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _to_wire_dict(value: AlgorithmConfig) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict"):
        return value.to_dict()
    raise TypeError("algorithm must be a mapping or expose to_dict()")


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
    return (
        isinstance(exc, MagickMindError) and exc.status_code in _RETRYABLE_STATUS_CODES
    )
