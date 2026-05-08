"""In-memory mock LLM router used when no vendor API keys are configured."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class MockLLMRouter:
    def __init__(self, provider: str = "anthropic") -> None:
        self.provider = LLMProvider(provider)
        self.call_count = 0

    async def query(
        self,
        prompt: str,
        context_docs: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        self.call_count += 1
        context_docs = context_docs or []
        return {
            "response": self._generate_response(prompt, context_docs),
            "provider": self.provider.value,
            "model": "mock-model",
            "tokens_used": {"prompt": 150, "completion": 200},
            "citations": [d.get("id", f"doc_{i}") for i, d in enumerate(context_docs)],
            "confidence": 0.85,
        }

    async def switch_provider(self, provider: str) -> None:
        self.provider = LLMProvider(provider)

    @staticmethod
    def _generate_response(prompt: str, context_docs: list[dict[str, Any]]) -> str:
        lines = [
            "Based on the provided medical knowledge base, here's a response to your query:",
            "",
            f"**Query:** {prompt}",
            "",
        ]
        if context_docs:
            lines.append(f"**Relevant Sources:** {len(context_docs)} document(s) found")
            lines.append("")
            lines.append("**Information Found:**")
            for i, doc in enumerate(context_docs, 1):
                preview = doc.get("text", "")[:100]
                lines.append(f"{i}. {preview}...")
        else:
            lines.append("No relevant documents found in the knowledge base.")
        lines.append("")
        lines.append(
            "_Note: this is a mock response generated in development mode. "
            "Real LLM responses will be generated when API keys are configured._"
        )
        return "\n".join(lines)

    async def health_check(self) -> bool:
        return True


_llm_router_instance: MockLLMRouter | None = None


async def get_llm_router(provider: str = "anthropic") -> MockLLMRouter:
    global _llm_router_instance
    if _llm_router_instance is None:
        _llm_router_instance = MockLLMRouter(provider)
    return _llm_router_instance
