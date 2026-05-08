"""MCP (Model Context Protocol) server exposing MedRAG tools.

Mounted onto the FastAPI app at /mcp via streamable-http transport so any
MCP-compatible client (Claude Desktop, Cursor, etc.) can call MedRAG tools
directly. Falls back to a JSON stub if the optional `mcp` SDK is missing.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)


def _build_real_mcp_app():
    """Build a streamable-http MCP server, or return None if SDK missing."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        return None

    from app.services import dedupe_retrieved_docs, get_llm_router, get_vector_store

    mcp = FastMCP("medrag", stateless_http=True)

    @mcp.tool()
    async def ingest_document(title: str, content: str) -> dict[str, Any]:
        """Ingest a medical document into the knowledge base.

        Args:
            title: Short human-readable title.
            content: Full text body.
        """
        vector_store = await get_vector_store()
        doc_id = f"doc_{abs(hash(title)) % 10000}"
        await vector_store.add_document(doc_id, content, {"title": title})
        return {"doc_id": doc_id, "title": title, "status": "ingested"}

    @mcp.tool()
    async def query(question: str, top_k: int = 3) -> dict[str, Any]:
        """Run a RAG query against the medical knowledge base.

        Args:
            question: Natural-language medical question.
            top_k: How many supporting documents to retrieve.
        """
        vector_store = await get_vector_store()
        docs = await vector_store.search(question, top_k=top_k)
        docs = dedupe_retrieved_docs(docs)
        llm = await get_llm_router()
        answer = await llm.query(question, docs)
        return {
            "question": question,
            "answer": answer,
            "sources": [
                {"id": d["id"], "score": d["score"], "metadata": d["metadata"]}
                for d in docs
            ],
        }

    @mcp.tool()
    async def list_documents() -> dict[str, Any]:
        """List every document currently tracked locally."""
        vector_store = await get_vector_store()
        return {
            "total": len(vector_store.documents),
            "documents": [
                {"id": did, "metadata": d["metadata"]}
                for did, d in vector_store.documents.items()
            ],
        }

    return mcp.streamable_http_app()


def _build_router() -> APIRouter:
    router = APIRouter(tags=["mcp"])

    @router.get("/mcp/info")
    async def mcp_info() -> dict[str, Any]:
        cursor_snippet = {
            "mcpServers": {
                "medrag": {
                    "url": "https://16-170-207-120.sslip.io/mcp",
                    "transport": "streamable-http",
                }
            }
        }

        claude_snippet = cursor_snippet

        return {
            "name": "medrag",
            "description": (
                "MedRAG MCP server exposes tools for medical-document ingestion, "
                "retrieval, and question answering over streamable-http."
            ),
            "what_is_mcp": (
                "MCP (Model Context Protocol) lets AI clients call external tools "
                "through a standard interface."
            ),
            "transport": "streamable-http",
            "endpoint": "/mcp",
            "live_endpoint": "https://16-170-207-120.sslip.io/mcp",
            "tools": [
                {
                    "name": "ingest_document",
                    "description": "Ingest a medical document (title + content)",
                    "args": {"title": "string", "content": "string"},
                },
                {
                    "name": "query",
                    "description": "Run RAG query over indexed documents",
                    "args": {"question": "string", "top_k": "int (default: 3)"},
                },
                {
                    "name": "list_documents",
                    "description": "List tracked documents",
                    "args": {},
                },
            ],
            "connect": {
                "cursor": {
                    "where": "Cursor Settings -> MCP Servers",
                    "snippet": cursor_snippet,
                },
                "claude_desktop": {
                    "where": "claude_desktop_config.json",
                    "snippet": claude_snippet,
                },
            },
            "copy_paste_snippet": cursor_snippet,
            "links": {
                "mcp_info": "/mcp/info",
                "docs": "/docs",
                "health": "/health",
            },
        }

    return router


mcp_app = _build_real_mcp_app()
mcp_router = _build_router()
