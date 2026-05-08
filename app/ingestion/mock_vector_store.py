"""In-memory mock vector store used when no Pinecone API key is configured."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

logger = logging.getLogger(__name__)


class MockVectorStore:
    """Tiny cosine-similarity-style retriever backed by hash embeddings."""

    def __init__(self) -> None:
        self.documents: dict[str, dict[str, Any]] = {}

    async def add_document(self, doc_id: str, text: str, metadata: dict | None = None) -> None:
        self.documents[doc_id] = {
            "text": text,
            "embedding": self._mock_embed(text),
            "metadata": metadata or {},
        }
        logger.info("added document %s", doc_id)

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not self.documents:
            return []
        query_embedding = self._mock_embed(query)
        results = [
            {
                "id": doc_id,
                "text": doc["text"],
                "score": self._cosine(query_embedding, doc["embedding"]),
                "metadata": doc["metadata"],
            }
            for doc_id, doc in self.documents.items()
        ]
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:top_k]

    async def delete_document(self, doc_id: str) -> None:
        self.documents.pop(doc_id, None)

    async def health_check(self) -> bool:
        return True

    @staticmethod
    def _mock_embed(text: str) -> list[float]:
        h = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [(h + i) % 100 / 100.0 for i in range(1536)]

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(y * y for y in b) ** 0.5
        denom = norm_a * norm_b
        return dot / denom if denom else 0.0


_vector_store_instance: MockVectorStore | None = None


async def get_vector_store() -> MockVectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = MockVectorStore()
    return _vector_store_instance
