"""HTTP API for the RAG knowledge base."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.services import dedupe_retrieved_docs, get_llm_router, get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["rag"])


@router.post("/ingest")
async def ingest_document(title: str, content: str) -> dict:
    """Add a document to the knowledge base."""
    if not title.strip():
        raise HTTPException(status_code=400, detail="title must not be empty")
    if not content.strip():
        raise HTTPException(status_code=400, detail="content must not be empty")

    vector_store = await get_vector_store()
    doc_id = f"doc_{abs(hash(title)) % 10000}"
    await vector_store.add_document(doc_id, content, {"title": title})
    return {
        "status": "ok",
        "doc_id": doc_id,
        "title": title,
        "message": "Document ingested successfully.",
    }


@router.post("/query")
async def query_rag(
    query: str,
    top_k: int = Query(default=3, ge=1, le=10, description="Number of documents to retrieve"),
) -> dict:
    """Run a retrieval-augmented query against the knowledge base."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")

    try:
        vector_store = await get_vector_store()
        relevant_docs = await vector_store.search(query, top_k=top_k)
        relevant_docs = dedupe_retrieved_docs(relevant_docs)
        llm = await get_llm_router()
        response = await llm.query(query, relevant_docs)
        return {
            "query": query,
            "top_k": top_k,
            "retrieved_docs_count": len(relevant_docs),
            "retrieved_docs": relevant_docs,
            "response": response,
        }
    except Exception as exc:
        logger.exception("query_failed")
        raise HTTPException(
            status_code=500,
            detail="Query failed. Verify API keys, backend connectivity, and request payload.",
        ) from exc


@router.get("/documents")
async def list_documents() -> dict:
    """Return every document currently tracked locally."""
    vector_store = await get_vector_store()
    docs = [
        {"id": doc_id, "preview": data["text"][:120], "metadata": data["metadata"]}
        for doc_id, data in vector_store.documents.items()
    ]
    return {"total": len(docs), "documents": docs}
