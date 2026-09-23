import asyncio
from types import SimpleNamespace

import httpx
import pytest
from openai import (
    APIConnectionError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
)

from screen_ocr.core.models import TranslationRequest
from screen_ocr.services import deepseek
from screen_ocr.services.deepseek import (
    DEEPSEEK_MODEL,
    SYSTEM_PROMPT,
    DeepSeekTranslationProvider,
)


class FakeCompletions:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.kwargs = None

    async def create(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return self.response


def fake_client(completions):
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


@pytest.mark.asyncio
async def test_deepseek_translates_with_non_thinking_prompt() -> None:
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="你好\n世界"))]
    )
    completions = FakeCompletions(response=response)
    provider = DeepSeekTranslationProvider("secret", client=fake_client(completions))
    result = await provider.translate(
        TranslationRequest("Hello\nWorld"), asyncio.Event()
    )
    assert result.text == "你好\n世界"
    assert completions.kwargs["model"] == DEEPSEEK_MODEL
    assert completions.kwargs["extra_body"] == {"thinking": {"type": "disabled"}}
    assert completions.kwargs["messages"][0]["content"] == SYSTEM_PROMPT
    assert completions.kwargs["messages"][1]["content"] == "Hello\nWorld"


@pytest.mark.asyncio
async def test_deepseek_rejects_empty_response() -> None:
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="  "))]
    )
    provider = DeepSeekTranslationProvider(
        "secret", client=fake_client(FakeCompletions(response=response))
    )
    result = await provider.translate(TranslationRequest("Hello"), asyncio.Event())
    assert result.text is None
    assert "没有返回译文" in result.error


@pytest.mark.asyncio
async def test_deepseek_maps_missing_client_credentials() -> None:
    provider = DeepSeekTranslationProvider("")
    result = await provider.translate(TranslationRequest("Hello"), asyncio.Event())
    assert result.text is None
    assert "重新保存 API Key" in result.error


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error_factory", "message"),
    [
        (
            lambda request: AuthenticationError(
                "bad key", response=httpx.Response(401, request=request), body=None
            ),
            "API Key 无效",
        ),
        (lambda request: APITimeoutError(request=request), "连接 DeepSeek 超时"),
        (
            lambda request: APIConnectionError(message="offline", request=request),
            "无法连接 DeepSeek",
        ),
        (
            lambda request: RateLimitError(
                "limited", response=httpx.Response(429, request=request), body=None
            ),
            "请求过于频繁",
        ),
    ],
)
async def test_deepseek_maps_common_errors(error_factory, message) -> None:
    request = httpx.Request("POST", "https://api.deepseek.com/chat/completions")
    provider = DeepSeekTranslationProvider(
        "secret",
        client=fake_client(FakeCompletions(error=error_factory(request))),
    )
    result = await provider.translate(TranslationRequest("Hello"), asyncio.Event())
    assert result.text is None
    assert message in result.error


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["connection", "timeout", 408, 409, 429, 500, 503])
@pytest.mark.parametrize("recover", [True, False])
async def test_network_retries_stop_at_tenth_attempt(monkeypatch, failure, recover):
    calls = []
    clients = []

    def handle(request):
        calls.append(request)
        if recover and len(calls) == 10:
            return httpx.Response(200, json={
                "id": "translation", "object": "chat.completion", "created": 0,
                "model": DEEPSEEK_MODEL,
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": "你好"}}],
            })
        if failure == "connection":
            raise httpx.ConnectError("offline", request=request)
        if failure == "timeout":
            raise httpx.ReadTimeout("timed out", request=request)
        return httpx.Response(failure, json={"error": {"message": "temporary error"}})

    def make_client(**kwargs):
        client = AsyncOpenAI(
            **kwargs, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle))
        )
        clients.append(client)
        return client

    monkeypatch.setattr(deepseek, "AsyncOpenAI", make_client)
    # Exercise the real SDK retry loop without waiting through its backoff.
    monkeypatch.setattr(AsyncOpenAI, "_calculate_retry_timeout", lambda *a, **kw: 0)
    result = await DeepSeekTranslationProvider("secret").translate(
        TranslationRequest("Hello"), asyncio.Event()
    )
    assert len(calls) == 10
    assert result.text == ("你好" if recover else None)
    assert bool(result.error) is not recover
    assert clients[0].is_closed()


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [200, 400, 401, 402, 403])
async def test_success_and_permanent_errors_do_not_retry(monkeypatch, status):
    calls = []

    def handle(request):
        calls.append(request)
        if status == 200:
            return httpx.Response(200, json={
                "id": "translation", "object": "chat.completion", "created": 0,
                "model": DEEPSEEK_MODEL,
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": "你好"}}],
            })
        return httpx.Response(status, json={"error": {"message": "invalid request"}})

    monkeypatch.setattr(deepseek, "AsyncOpenAI", lambda **kwargs: AsyncOpenAI(
        **kwargs, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle))
    ))
    result = await DeepSeekTranslationProvider("secret").translate(
        TranslationRequest("Hello"), asyncio.Event()
    )
    assert len(calls) == 1
    assert result.text == ("你好" if status == 200 else None)
    assert bool(result.error) == (status != 200)
