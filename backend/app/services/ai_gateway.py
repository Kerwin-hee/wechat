"""AI 服务网关 — 对接 OpenAI / DeepSeek，支持 SSE 流式输出与 Fallback"""

import asyncio
import json
import logging
import time
from typing import AsyncIterator

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AIProvider:
    """AI 供应商配置"""

    def __init__(
        self,
        name: str,
        api_key: str,
        base_url: str,
        model: str,
    ):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    @property
    def chat_url(self) -> str:
        return f"{self.base_url}/chat/completions"

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }


class AIGateway:
    """AI 网关：多供应商 + Fallback + 流式代理"""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._providers: list[AIProvider] = []
        self._init_providers()

    def _init_providers(self) -> None:
        if settings.OPENAI_API_KEY:
            self._providers.append(
                AIProvider(
                    name="openai",
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_BASE_URL,
                    model=settings.OPENAI_MODEL,
                )
            )
        if settings.DEEPSEEK_API_KEY:
            self._providers.append(
                AIProvider(
                    name="deepseek",
                    api_key=settings.DEEPSEEK_API_KEY,
                    base_url=settings.DEEPSEEK_BASE_URL,
                    model=settings.DEEPSEEK_MODEL,
                )
            )
        # 按配置的主供应商排序
        primary = settings.AI_PRIMARY_PROVIDER
        self._providers.sort(key=lambda p: 0 if p.name == primary else 1)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.AI_REQUEST_TIMEOUT),
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def chat_completion(
        self,
        messages: list[dict],
        stream: bool = False,
        max_tokens: int | None = None,
        temperature: float = 0.7,
    ) -> dict:
        """非流式请求，自动 Fallback"""
        last_error: str = ""
        for provider in self._providers:
            try:
                return await self._call_provider(
                    provider, messages, stream=False, max_tokens=max_tokens, temperature=temperature
                )
            except Exception as e:
                logger.warning("AI provider %s failed: %s", provider.name, e)
                last_error = str(e)
                continue
        raise RuntimeError(f"所有 AI 供应商均不可用: {last_error}")

    async def chat_completion_stream(
        self,
        messages: list[dict],
        max_tokens: int | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """流式请求，逐 token yield，自动 Fallback"""
        last_error: str = ""
        for provider in self._providers:
            try:
                async for token in self._call_provider_stream(
                    provider, messages, max_tokens=max_tokens, temperature=temperature
                ):
                    yield token
                return  # 成功，退出
            except Exception as e:
                logger.warning("AI provider %s stream failed: %s", provider.name, e)
                last_error = str(e)
                continue
        # 所有供应商都失败
        yield json.dumps({"error": f"所有 AI 供应商均不可用: {last_error}"})

    async def _call_provider(
        self,
        provider: AIProvider,
        messages: list[dict],
        stream: bool = False,
        max_tokens: int | None = None,
        temperature: float = 0.7,
    ) -> dict:
        client = await self._get_client()
        payload = {
            "model": provider.model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        else:
            payload["max_tokens"] = settings.AI_MAX_TOKENS_DEFAULT

        start = time.monotonic()
        resp = await client.post(provider.chat_url, headers=provider.headers, json=payload)
        elapsed = time.monotonic() - start
        logger.info("AI call %s: %d (%dms)", provider.name, resp.status_code, int(elapsed * 1000))

        if resp.status_code != 200:
            text = await resp.aread()
            raise RuntimeError(f"{provider.name} 返回 {resp.status_code}: {text[:500]}")
        return resp.json()

    async def _call_provider_stream(
        self,
        provider: AIProvider,
        messages: list[dict],
        max_tokens: int | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        client = await self._get_client()
        payload = {
            "model": provider.model,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        else:
            payload["max_tokens"] = settings.AI_MAX_TOKENS_DEFAULT

        start = time.monotonic()
        async with client.stream(
            "POST", provider.chat_url, headers=provider.headers, json=payload
        ) as resp:
            if resp.status_code != 200:
                text = await resp.aread()
                raise RuntimeError(f"{provider.name} 返回 {resp.status_code}: {text[:500]}")

            first_token = True
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        if first_token:
                            ttft = time.monotonic() - start
                            logger.info("AI stream first token: %dms", int(ttft * 1000))
                            first_token = False
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue


# 全局单例
_ai_gateway: AIGateway | None = None


def get_ai_gateway() -> AIGateway:
    global _ai_gateway
    if _ai_gateway is None:
        _ai_gateway = AIGateway()
    return _ai_gateway
