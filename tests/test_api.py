"""Smoke tests for the live FastAPI app."""

from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["mode"] in {"mock", "production"}


def test_landing_page() -> None:
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "MedRAG" in r.text


def test_mcp_info() -> None:
    client = TestClient(app)
    r = client.get("/mcp/info")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "medrag"
    tool_names = {t["name"] for t in body["tools"]}
    assert {"ingest_document", "query", "list_documents"}.issubset(tool_names)


def test_ingest_query_documents_roundtrip() -> None:
    client = TestClient(app)

    r = client.post(
        "/api/v1/ingest",
        params={"title": "Diabetes", "content": "Type 2 diabetes affects glucose metabolism."},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    r = client.get("/api/v1/documents")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post("/api/v1/query", params={"query": "diabetes glucose"})
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == "diabetes glucose"
    assert "response" in body
    assert isinstance(body["retrieved_docs"], list)
