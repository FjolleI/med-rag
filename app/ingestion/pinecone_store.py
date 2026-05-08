"""Pinecone integrated-index vector store.

Used when a real PINECONE_API_KEY is configured. The index must be an
*integrated* index (e.g. created with `llama-text-embed-v2` or
`multilingual-e5-large`) so Pinecone embeds text on the fly — no embedding
SDK required client-side.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from pinecone import Pinecone

logger = logging.getLogger(__name__)


class PineconeStore:
    """Async-friendly wrapper around an integrated Pinecone index."""

    def __init__(
        self,
        api_key: str,
        index_name: str,
        namespace: str = "__default__",
        text_field: str = "chunk_text",
    ) -> None:
        self._pc = Pinecone(api_key=api_key)
        self._index = self._pc.Index(index_name)
        self.index_name = index_name
        self.namespace = namespace
        self.text_field = text_field
        self.documents: dict[str, dict[str, Any]] = {}

    async def add_document(
        self, doc_id: str, text: str, metadata: dict[str, Any] | None = None
    ) -> None:
        record = {"_id": doc_id, self.text_field: text, **(metadata or {})}
        await asyncio.to_thread(
            lambda: self._index.upsert_records(records=[record], namespace=self.namespace)
        )
        self.documents[doc_id] = {"text": text, "metadata": metadata or {}}
        logger.info("upserted %s into %s/%s", doc_id, self.index_name, self.namespace)

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        result = await asyncio.to_thread(
            lambda: self._index.search_records(
                namespace=self.namespace,
                top_k=top_k,
                inputs={"text": query},
            )
        )
        raw_hits = self._extract_hits(result)
        hits: list[dict[str, Any]] = []
        for hit in raw_hits:
            fields, hit_id, score = self._unpack_hit(hit)
            text = fields.pop(self.text_field, "")
            hits.append(
                {
                    "id": hit_id,
                    "text": text,
                    "score": float(score) if score is not None else 0.0,
                    "metadata": fields,
                }
            )
        return hits

    @staticmethod
    def _extract_hits(result: Any) -> list[Any]:
        if isinstance(result, dict):
            return result.get("result", {}).get("hits", [])
        inner = getattr(result, "result", result)
        return list(getattr(inner, "hits", []) or [])

    @staticmethod
    def _unpack_hit(hit: Any) -> tuple[dict[str, Any], str | None, float | None]:
        if isinstance(hit, dict):
            fields = dict(hit.get("fields", {}) or {})
            hit_id = hit.get("id") or hit.get("_id")
            score = hit.get("score") if hit.get("score") is not None else hit.get("_score")
            return fields, hit_id, score
        fields = dict(getattr(hit, "fields", {}) or {})
        hit_id = getattr(hit, "id", None) or getattr(hit, "_id", None)
        score = getattr(hit, "score", None)
        if score is None:
            score = getattr(hit, "_score", None)
        return fields, hit_id, score

    async def delete_document(self, doc_id: str) -> None:
        await asyncio.to_thread(self._index.delete, ids=[doc_id], namespace=self.namespace)
        self.documents.pop(doc_id, None)

    async def health_check(self) -> bool:
        try:
            await asyncio.to_thread(self._index.describe_index_stats)
            return True
        except Exception:
            logger.exception("pinecone health check failed")
            return False


_instance: PineconeStore | None = None


async def get_pinecone_store(
    api_key: str,
    index_name: str,
    namespace: str = "__default__",
    text_field: str = "chunk_text",
) -> PineconeStore:
    global _instance
    if _instance is None:
        t0 = time.monotonic()
        _instance = PineconeStore(api_key, index_name, namespace, text_field)
        logger.info("connected to Pinecone index %s in %.2fs", index_name, time.monotonic() - t0)
    return _instance
