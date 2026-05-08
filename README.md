# MedRAG

Hosted **Retrieval-Augmented Generation** service with a built-in **Model Context Protocol** server. Drop the URL into Claude Desktop, Cursor, or any other MCP-aware client and you get three tools — `ingest_document`, `query`, `list_documents` — backed by a FastAPI app, Postgres, Redis, and a free-tier-friendly EC2 deploy.

```
┌─ Browser / MCP client ─┐
│                         │
└─────┬───────────────────┘
      │  HTTPS (auto-cert via Caddy + Let's Encrypt)
┌─────▼─────────────────────────────────────────────┐
│            EC2 box · docker compose               │
│  caddy ──► api (FastAPI + MCP) ──► postgres       │
│                                  └► redis         │
└───────────────────────────────────────────────────┘
```

| Surface | URL |
|---|---|
| Landing page + interactive demo | `https://<domain>/` |
| OpenAPI / Swagger | `https://<domain>/docs` |
| MCP streamable-http endpoint | `https://<domain>/mcp` |
| MCP capabilities (JSON) | `https://<domain>/mcp/info` |
| Health check | `https://<domain>/health` |

## Quickstart

### Local (no Docker)

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
# open http://localhost:8000
```

### Local (Docker, full stack)

```bash
cp .env.example .env
docker compose -f docker-compose.dev.yml up --build
```

Compose keeps PostgreSQL/Redis URLs on the Docker network (`postgres`, `redis`); other variables come from `.env`.

### Production (AWS EC2)

See [DEPLOYMENT.md](./DEPLOYMENT.md) for the full walkthrough. TL;DR:

```bash
ssh ec2-user@<ip>
curl -fsSL https://raw.githubusercontent.com/<you>/medrag/main/deploy/bootstrap-ec2.sh | bash
git clone https://github.com/<you>/medrag.git && cd medrag
cp .env.prod.example .env && $EDITOR .env
./deploy/deploy.sh
```

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/ingest?title=…&content=…` | Add a document to the knowledge base |
| `POST` | `/api/v1/query?query=…&top_k=3` | RAG query, returns retrieved docs + answer |
| `GET`  | `/api/v1/documents` | List every ingested document |
| `GET`  | `/health` | Health check |
| `GET`  | `/mcp/info` | MCP capabilities & client config snippet |

## Connect from an MCP client

```json
{
  "mcpServers": {
    "medrag": {
      "url": "https://<your-domain>/mcp",
      "transport": "streamable-http"
    }
  }
}
```

Restart the client; the three MedRAG tools appear automatically.

## Stack

- Python 3.11, FastAPI, Uvicorn
- Model Context Protocol via the official `mcp` Python SDK (streamable HTTP)
- PostgreSQL 15, Redis 7
- Docker, docker-compose
- Caddy 2 (auto-HTTPS via Let's Encrypt)
- Optional: Pinecone, Anthropic Claude, OpenAI GPT-4o (set keys in `.env` to leave mock mode)

## Mock vs production mode

The service starts in **mock mode** by default — an in-memory vector store and canned LLM responses make the deploy useful as a portfolio link without any third-party costs. Set real `PINECONE_API_KEY`, `ANTHROPIC_API_KEY`, and `OPENAI_API_KEY` in `.env` to flip the same image into production mode.

## Layout

```
medrag/
├── app/
│   ├── main.py              FastAPI factory + /health + landing
│   ├── mcp_server.py        MCP tools + /mcp streamable-http mount
│   ├── routers/demo.py      /api/v1/{ingest,query,documents}
│   ├── ingestion/           mock_vector_store.py
│   ├── rag/                 mock_llm.py
│   └── static/              landing page (HTML + CSS + JS)
├── tests/                   pytest smoke tests
├── deploy/                  Caddyfile + EC2 bootstrap + deploy.sh
├── Dockerfile
├── docker-compose.dev.yml   local dev stack
├── docker-compose.prod.yml  EC2 prod stack with Caddy
├── DEPLOYMENT.md            EC2 walkthrough
└── README.md
```

## Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## License

MIT
