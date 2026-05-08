# MedRAG

> **Production-grade medical RAG + MCP system showcase**  
> Upload domain documents, retrieve evidence-backed context, and query through both a modern chat UI and MCP tools.

![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-Streamable_HTTP-6E56CF)
![AWS](https://img.shields.io/badge/AWS-EC2-FF9900?logo=amazonaws&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## Live Demo

- **Web app:** `https://16-170-207-120.sslip.io/`
- **API docs:** `https://16-170-207-120.sslip.io/docs`
- **MCP endpoint:** `https://16-170-207-120.sslip.io/mcp`
- **MCP info:** `https://16-170-207-120.sslip.io/mcp/info`
- **Health:** `https://16-170-207-120.sslip.io/health`

> You can replace these with your own domain after redeploy:
> - `https://<your-domain>/`
> - `https://<your-domain>/mcp`

## What This Showcases

- Startup-grade AI product UX with a chat-style web demo
- Retrieval-augmented generation (RAG) over ingestible documents
- MCP server integration for Cursor / Claude Desktop tool calling
- Real backend mode (Pinecone + OpenAI) and zero-cost mock mode
- Production deployment blueprint on AWS EC2 + Caddy auto-HTTPS

## How It Works

```text
                        +------------------------------+
                        |  Browser / Cursor / Claude  |
                        +---------------+--------------+
                                        |
                              HTTPS (Caddy + TLS)
                                        |
                      +-----------------v------------------+
                      |        FastAPI (MedRAG API)        |
                      |  /api/v1/*   /mcp   /mcp/info      |
                      +-----------+---------------+---------+
                                  |               |
                          retrieval|               |tool calls
                                  |               |
                     +------------v---+      +----v----------------+
                     | Pinecone Index |      |  MCP Streamable-HTTP|
                     | (integrated)   |      |  (ingest/query/list)|
                     +----------------+      +----------------------+
                                  |
                         context chunks
                                  |
                           +------v------+
                           | OpenAI LLM  |
                           +-------------+
```

## Try It (Step-by-step)

### 1) Local (no Docker)

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000`.

### 2) Local (Docker full stack)

```bash
cp .env.example .env
docker compose -f docker-compose.dev.yml up --build
```

### 3) Use the demo flow

1. Ingest a document (`Upload document` panel)
2. Ask a clinical-style question (`Ask MedRAG`)
3. Inspect retrieved docs and citations in response payload

### 4) Connect an MCP client

Use this in Cursor MCP settings or `claude_desktop_config.json`:

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

## Example API Calls

### Ingest

```bash
curl -X POST "https://16-170-207-120.sslip.io/api/v1/ingest?title=Diabetes%20Overview&content=Type%202%20diabetes%20is%20a%20chronic%20condition..."
```

### Query

```bash
curl -X POST "https://16-170-207-120.sslip.io/api/v1/query?query=What%20is%20first-line%20treatment%20for%20type%202%20diabetes?&top_k=3"
```

### List indexed docs

```bash
curl "https://16-170-207-120.sslip.io/api/v1/documents"
```

### Health

```bash
curl "https://16-170-207-120.sslip.io/health"
```

## Use Cases

- **Medical RAG assistant** for guideline-grounded Q&A
- **Document QA sandbox** for domain-specific corpora
- **MCP integration demo** for AI tool-calling workflows
- **Portfolio backend showcase** combining infra, API, UX, and AI

## Tech Stack

- **Backend:** Python 3.11, FastAPI, Uvicorn
- **AI protocol:** MCP (`mcp` Python SDK, streamable HTTP transport)
- **Vector retrieval:** Pinecone integrated index
- **Generation:** OpenAI Chat Completions (`gpt-4o-mini` default)
- **State/storage:** PostgreSQL 15, Redis 7 (compose stack)
- **Infra:** Docker, Docker Compose, Caddy, AWS EC2
- **Testing:** Pytest

## Demo Assets (placeholders)

> Add screenshots/GIFs in `docs/assets/` and update links below.

- `docs/assets/hero-ui.png` — landing + chat interface
- `docs/assets/ingest-flow.gif` — upload document -> indexed
- `docs/assets/query-flow.gif` — query -> retrieved context -> answer
- `docs/assets/mcp-connect.png` — MCP config in Cursor/Claude

## Production Deploy

Full guide: [DEPLOYMENT.md](./DEPLOYMENT.md)

Quick deploy:

```bash
ssh ec2-user@<ec2-public-ip>
curl -fsSL https://raw.githubusercontent.com/FjolleI/med-rag/main/deploy/bootstrap-ec2.sh | bash
git clone https://github.com/FjolleI/med-rag.git && cd medrag
cp .env.prod.example .env && $EDITOR .env
./deploy/deploy.sh
```

## Modes: Mock vs Real

- **Mock mode** (`mock-dev` keys): no paid dependencies, ideal for demos
- **Real mode**: set `PINECONE_API_KEY` + `OPENAI_API_KEY` and redeploy

## Repository Layout

```text
medrag/
├── app/
│   ├── main.py
│   ├── mcp_server.py
│   ├── routers/demo.py
│   ├── services.py
│   ├── ingestion/
│   ├── rag/
│   └── static/
├── deploy/
├── tests/
├── docker-compose.dev.yml
├── docker-compose.prod.yml
└── DEPLOYMENT.md
```

## Run Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## License

MIT
