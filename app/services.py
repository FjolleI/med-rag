"""Service factories: pick real or mock backends from settings."""

from __future__ import annotations

import logging
from typing import Any, Protocol

logger = logging.getLogger(__name__)
_logged_missing_pinecone = False
_logged_missing_openai = False
_logged_anthropic_stub = False


def _is_placeholder(value: str | None) -> bool:
    if not value:
        return True
    v = value.strip().lower()
    return v.startswith(("mock", "your-", "sk-...", "...")) or v in {"changeme", "change-me"}


def dedupe_retrieved_docs(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop duplicate/near-duplicate retrieval results while preserving order.

    Uses normalized text content as the primary key and falls back to document id.
    """
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []

    for doc in docs:
        text_key = " ".join((doc.get("text") or "").lower().split())
        if text_key:
            key = f"text:{text_key}"
        else:
            key = f"id:{doc.get('id', '')}"

        if key in seen:
            continue
        seen.add(key)
        unique.append(doc)

    return unique


class VectorStore(Protocol):
    documents: dict[str, dict[str, Any]]

    async def add_document(self, doc_id: str, text: str, metadata: dict[str, Any] | None = None) -> None: ...
    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]: ...
    async def health_check(self) -> bool: ...


class LLMRouter(Protocol):
    async def query(
        self, prompt: str, context_docs: list[dict[str, Any]] | None = None, temperature: float = 0.7
    ) -> dict[str, Any]: ...


async def get_vector_store() -> VectorStore:
    global _logged_missing_pinecone
    from app.main import settings

    if not _is_placeholder(settings.pinecone_api_key):
        try:
            from app.ingestion.pinecone_store import get_pinecone_store

            return await get_pinecone_store(
                api_key=settings.pinecone_api_key,
                index_name=settings.pinecone_index,
                namespace=settings.pinecone_namespace,
                text_field=settings.pinecone_text_field,
            )
        except ModuleNotFoundError as exc:
            if exc.name == "pinecone":
                if not _logged_missing_pinecone:
                    logger.warning(
                        "Pinecone SDK not installed; falling back to mock vector store. "
                        "Install with: pip install -r requirements.txt"
                    )
                    _logged_missing_pinecone = True
            else:
                logger.exception("Vector store dependency missing; falling back to mock vector store")
        except Exception:
            logger.exception("Pinecone init failed; falling back to mock vector store")

    from app.ingestion.mock_vector_store import get_vector_store as get_mock_store

    return await get_mock_store()


async def get_llm_router() -> LLMRouter:
    global _logged_missing_openai, _logged_anthropic_stub
    from app.main import settings

    provider = settings.llm_provider.lower()

    if provider == "openai" and not _is_placeholder(settings.openai_api_key):
        try:
            from app.rag.openai_llm import get_openai_llm

            return await get_openai_llm(api_key=settings.openai_api_key, model=settings.openai_model)
        except ModuleNotFoundError as exc:
            if exc.name == "openai":
                if not _logged_missing_openai:
                    logger.warning(
                        "OpenAI SDK not installed; falling back to mock LLM. "
                        "Install with: pip install -r requirements.txt"
                    )
                    _logged_missing_openai = True
            else:
                logger.exception("LLM dependency missing; falling back to mock LLM")
        except Exception:
            logger.exception("OpenAI init failed; falling back to mock LLM")

    if provider == "anthropic" and not _is_placeholder(settings.anthropic_api_key):
        if not _logged_anthropic_stub:
            logger.warning("Anthropic backend not implemented; using mock")
            _logged_anthropic_stub = True

    from app.rag.mock_llm import get_llm_router as get_mock_llm

    return await get_mock_llm(provider)


def is_mock_mode() -> bool:
    """True if either the vector store or the LLM is still using a mock backend."""
    from app.main import settings

    pine_real = not _is_placeholder(settings.pinecone_api_key)
    if settings.llm_provider.lower() == "openai":
        llm_real = not _is_placeholder(settings.openai_api_key)
    else:
        llm_real = not _is_placeholder(settings.anthropic_api_key)
    return not (pine_real and llm_real)
