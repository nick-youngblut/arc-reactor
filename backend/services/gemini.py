from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, AsyncIterator

from langchain.chat_models import init_chat_model

from ..utils.circuit_breaker import Breakers


def _use_vertex_ai(settings: object) -> bool:
    if os.getenv("GOOGLE_CLOUD_PROJECT"):
        return True
    return bool(getattr(settings, "google_cloud_project", None))


@dataclass
class GeminiService:
    model: Any
    breaker: object

    @classmethod
    def create(cls, settings: object, breakers: Breakers) -> "GeminiService":
        model_id = getattr(settings, "gemini_model", "gemini-3-flash-preview")
        thinking_level = getattr(settings, "gemini_thinking_level", "low")
        provider = "google_vertexai" if _use_vertex_ai(settings) else "google_genai"

        model = init_chat_model(
            f"{provider}:{model_id}",
            temperature=1.0,
            thinking_level=thinking_level,
        )
        return cls(model=model, breaker=breakers.gemini)

    async def complete(self, messages: list[Any]) -> Any:
        @self.breaker
        async def _run() -> Any:
            return await self.model.ainvoke(messages)

        return await _run()

    async def stream_text(self, messages: list[Any]) -> AsyncIterator[str]:
        @self.breaker
        async def _collect() -> list[str]:
            chunks: list[str] = []
            async for chunk in self.model.astream(messages):
                content = getattr(chunk, "content", chunk)
                if isinstance(content, str):
                    chunks.append(content)
                    continue
                blocks = getattr(chunk, "content_blocks", None)
                if blocks:
                    for block in blocks:
                        if block.get("type") == "text":
                            chunks.append(block.get("text", ""))
            return chunks

        for text in await _collect():
            if text:
                yield text

    async def health_check(self) -> bool:
        try:
            await self.complete([{"role": "user", "content": "ping"}])
            return True
        except Exception:
            return False


@dataclass
class DisabledGeminiService:
    error: Exception | None = None

    async def complete(self, messages: list[Any]) -> Any:
        raise RuntimeError("Gemini service is not configured") from self.error

    async def stream_text(self, messages: list[Any]) -> AsyncIterator[str]:
        if False:
            yield ""

    async def health_check(self) -> bool:
        return False
