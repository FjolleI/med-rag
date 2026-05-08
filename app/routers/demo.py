"""HTTP API for the RAG knowledge base."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.services import get_llm_router, get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["rag"])


@router.post("/ingest")
async def ingest_document(title: str, content: str) -> dict:
    """Add a document to the knowledge base."""
    vector_store = await get_vector_store()
    doc_id = f"doc_{abs(hash(title)) % 10000}"
    await vector_store.add_document(doc_id, content, {"title": title})
    return {"status": "ok", "doc_id": doc_id, "title": title}


@router.post("/query")
async def query_rag(query: str, top_k: int = 3) -> dict:
    """Run a retrieval-augmented query against the knowledge base."""
    try:
        vector_store = await get_vector_store()
        relevant_docs = await vector_store.search(query, top_k=top_k)
        llm = await get_llm_router()
        response = await llm.query(query, relevant_docs)
        return {"query": query, "retrieved_docs": relevant_docs, "response": response}
    except Exception as exc:
        logger.exception("query_failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/documents")
async def list_documents() -> dict:
    """Return every document currently tracked locally."""
    vector_store = await get_vector_store()
    docs = [
        {"id": doc_id, "preview": data["text"][:120], "metadata": data["metadata"]}
        for doc_id, data in vector_store.documents.items()
    ]
    return {"total": len(docs), "documents": docs}
