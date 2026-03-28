"""Unified LLM backend abstraction for HYDRA multi-provider debate.

Supports Claude (Anthropic), GPT-4o (OpenAI), and Gemini (Google)
through a single async interface. Using different providers for
different debate agents creates genuine cognitive diversity.

Reference: "Wisdom of the Silicon Crowd" (Science Advances, 2024)
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod

from chimera.config import settings


class LLMBackend(ABC):
    """Abstract LLM backend interface."""

    @abstractmethod
    async def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """Generate a completion and return the text."""
        ...

    @abstractmethod
    async def complete_json(
        self,
        system: str,
        user: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> dict:
        """Generate a completion and parse as JSON."""
        ...


class AnthropicBackend(LLMBackend):
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._client

    async def complete(self, system: str, user: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
        client = self._get_client()
        response = await client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text

    async def complete_json(self, system: str, user: str, temperature: float = 0.7, max_tokens: int = 500) -> dict:
        text = await self.complete(system, user, temperature, max_tokens)
        return _extract_json(text)


class OpenAIBackend(LLMBackend):
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import openai
            self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def complete(self, system: str, user: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""

    async def complete_json(self, system: str, user: str, temperature: float = 0.7, max_tokens: int = 500) -> dict:
        text = await self.complete(system, user, temperature, max_tokens)
        return _extract_json(text)


class GeminiBackend(LLMBackend):
    def __init__(self, model: str = "gemini-2.0-flash"):
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import google.generativeai as genai
            genai.configure(api_key=settings.google_api_key)
            self._client = genai.GenerativeModel(self.model)
        return self._client

    async def complete(self, system: str, user: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
        import asyncio
        client = self._get_client()
        prompt = f"System instructions: {system}\n\n{user}"
        response = await asyncio.to_thread(
            client.generate_content,
            prompt,
            generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
        )
        return response.text

    async def complete_json(self, system: str, user: str, temperature: float = 0.7, max_tokens: int = 500) -> dict:
        text = await self.complete(system, user, temperature, max_tokens)
        return _extract_json(text)


def create_backend(backend_name: str, model: str) -> LLMBackend:
    """Factory function to create LLM backends."""
    backends = {
        "anthropic": AnthropicBackend,
        "openai": OpenAIBackend,
        "google": GeminiBackend,
    }
    backend_cls = backends.get(backend_name)
    if not backend_cls:
        raise ValueError(f"Unknown backend: {backend_name}. Choose from: {list(backends.keys())}")
    return backend_cls(model=model)


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        return json.loads(text[start:end].strip())

    if "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        return json.loads(text[start:end].strip())

    # Try finding JSON object boundaries
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])

    return {"error": "Failed to parse JSON", "raw": text}
