"""OpenAI Chat Completions LLM router used in production mode."""

from __future__ import annotations

import logging
from typing import Any

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are MedRAG, a careful medical information assistant. Answer the user's "
    "question using ONLY the provided context passages. If the context does not "
    "contain the answer, say so plainly. Always cite the source IDs you used in "
    "the format [doc_id]. Do not invent facts. Remind the user that this is "
    "informational and not medical advice."
)


class OpenAILLM:
    """Real OpenAI-backed LLM router."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.provider = "openai"
        self.call_count = 0

    async def query(
        self,
        prompt: str,
        context_docs: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        self.call_count += 1
        context_docs = context_docs or []

        context_block = self._format_context(context_docs)
        user_message = f"Context:\n{context_block}\n\nQuestion: {prompt}"

        completion = await self._client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )

        choice = completion.choices[0]
        usage = completion.usage
        return {
            "response": choice.message.content or "",
            "provider": self.provider,
            "model": completion.model,
            "tokens_used": {
                "prompt": getattr(usage, "prompt_tokens", 0),
                "completion": getattr(usage, "completion_tokens", 0),
            },
            "citations": [d.get("id", f"doc_{i}") for i, d in enumerate(context_docs)],
            "finish_reason": choice.finish_reason,
        }

    @staticmethod
    def _format_context(docs: list[dict[str, Any]]) -> str:
        if not docs:
            return "(no documents retrieved)"
        chunks = []
        for d in docs:
            doc_id = d.get("id", "?")
            text = d.get("text", "")
            chunks.append(f"[{doc_id}] {text}")
        return "\n\n".join(chunks)

    async def switch_provider(self, provider: str) -> None:
        self.provider = provider

    async def health_check(self) -> bool:
        return True


_instance: OpenAILLM | None = None


async def get_openai_llm(api_key: str, model: str = "gpt-4o-mini") -> OpenAILLM:
    global _instance
    if _instance is None:
        _instance = OpenAILLM(api_key=api_key, model=model)
        logger.info("OpenAI LLM router ready (model=%s)", model)
    return _instance
