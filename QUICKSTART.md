# Quickstart

Three ways to run MedRAG, fastest first.

## 1. Bare Python (no Docker)

```powershell
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000`.

## 2. Docker Compose (full stack)

Create `.env` first (the API service reads it; database URLs are overridden for in-container networking):

```powershell
copy .env.example .env
docker compose -f docker-compose.dev.yml up --build
```

Stops the stack with `Ctrl+C`, brings it down with `docker compose -f docker-compose.dev.yml down`.

## 3. EC2 production deploy

See [DEPLOYMENT.md](./DEPLOYMENT.md).

Live deployment:
- App: `https://16-170-207-120.sslip.io/`
- Docs: `https://16-170-207-120.sslip.io/docs`
- MCP: `https://16-170-207-120.sslip.io/mcp`

## Smoke-test the API

```powershell
curl http://localhost:8000/health
curl -X POST "http://localhost:8000/api/v1/ingest?title=Diabetes&content=Type%202%20diabetes%20affects%20glucose%20metabolism."
curl -X POST "http://localhost:8000/api/v1/query?query=What%20is%20diabetes"
curl http://localhost:8000/api/v1/documents
```

Or use the interactive UI at `http://localhost:8000` and the OpenAPI explorer at `http://localhost:8000/docs`.

## Add to an MCP client

```json
{
  "mcpServers": {
    "medrag": {
      "url": "https://16-170-207-120.sslip.io/mcp",
      "transport": "streamable-http"
    }
  }
}
```

## Going from mock to real LLMs

Edit `.env` and replace the `mock-dev` values with real API keys:

```
PINECONE_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

Then swap the imports in `app/routers/demo.py` and `app/mcp_server.py` from `mock_vector_store` / `mock_llm` to your real implementations.

## Run tests

```powershell
pytest tests/ -v
```
