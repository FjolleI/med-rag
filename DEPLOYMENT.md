# Deploying MedRAG to AWS EC2

End-to-end recipe for shipping the project as a **hosted MCP server + web demo**
on a single EC2 box, with free auto-HTTPS and no domain registration required.

```
┌──────────── EC2 instance (t3.small or larger) ─────────────┐
│                                                            │
│   Caddy  ──┐    443 / 80                                   │
│            │   (auto-HTTPS via Let's Encrypt)              │
│            ▼                                               │
│   ┌────────────────┐    ┌──────────────┐   ┌────────────┐  │
│   │  FastAPI app   │───▶│  PostgreSQL  │   │   Redis    │  │
│   │  / (landing)   │    │              │   │            │  │
│   │  /docs         │    └──────────────┘   └────────────┘  │
│   │  /api/v1/*     │                                       │
│   │  /mcp  (MCP)   │                                       │
│   └────────────────┘                                       │
└────────────────────────────────────────────────────────────┘
```

---

## 1. Prepare the EC2 instance

### Recommended baseline

| Setting           | Value                                    |
| ----------------- | ---------------------------------------- |
| AMI               | Amazon Linux 2023 (or Ubuntu 22.04+)     |
| Instance type     | `t3.small` (2 vCPU, 2 GB) — minimum      |
| Storage           | 20 GB gp3                                |
| Security group    | Allow inbound `22`, `80`, `443` from `0.0.0.0/0` |
| Public IPv4       | Yes (required for the free domain trick) |

> Why `t3.small`? Compose stack runs Postgres + Redis + Caddy + FastAPI;
> `t3.micro` (1 GB) will OOM during the first build.

### SSH in

```bash
ssh -i your-key.pem ec2-user@<ec2-public-ip>      # Amazon Linux
# or
ssh -i your-key.pem ubuntu@<ec2-public-ip>        # Ubuntu
```

---

## 2. Bootstrap Docker

```bash
curl -fsSLO https://raw.githubusercontent.com/<you>/medrag/main/deploy/bootstrap-ec2.sh
bash bootstrap-ec2.sh
exec sudo -u "$USER" bash -l        # pick up new docker group membership
```

Verify:

```bash
docker --version
docker compose version
```

---

## 3. Clone & configure

```bash
git clone https://github.com/<you>/medrag.git
cd medrag
cp .env.prod.example .env
```

Generate secrets and pick a domain:

```bash
# JWT secret
sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$(openssl rand -hex 32)|" .env

# Postgres password
sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -hex 16)|" .env

# Free domain via sslip.io — uses your public IP, no registration
PUBLIC_IP=$(curl -s ifconfig.me)
sed -i "s|DOMAIN=.*|DOMAIN=${PUBLIC_IP//./-}.sslip.io|" .env

cat .env | grep -E '^(DOMAIN|JWT|POSTGRES_PASSWORD)='
```

Result looks like `DOMAIN=3-86-12-204.sslip.io`. That hostname automatically
resolves to your EC2 IP — no DNS account, no propagation wait.

> **If you'd rather use DuckDNS:** create a free subdomain at
> <https://www.duckdns.org>, point it at your IP, then set `DOMAIN=yourname.duckdns.org`.

---

## 4. Deploy

```bash
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

The script will:

1. Build the API image.
2. Start `caddy`, `api`, `postgres`, `redis`.
3. Wait for `/health` to return `200`.
4. Print every public URL.

The first HTTPS request takes 10–30 seconds while Caddy provisions a
Let's Encrypt certificate. Subsequent requests are instant and certs auto-renew.

---

## 5. Verify

Open in your browser:

| URL                              | What you should see                                   |
| -------------------------------- | ----------------------------------------------------- |
| `https://<domain>/`              | Landing page with interactive demo                    |
| `https://<domain>/docs`          | Swagger / OpenAPI explorer                            |
| `https://<domain>/health`        | `{"status":"ok",...}`                                 |
| `https://<domain>/mcp/info`      | MCP capabilities + ready-to-paste client config       |
| `https://<domain>/mcp`           | MCP streamable-http endpoint (HTTP 405 in a browser — that's expected; it speaks JSON-RPC over POST/SSE) |

---

## 6. Connect from an MCP client

Add to `claude_desktop_config.json` (or Cursor's MCP settings):

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

Restart the client. Three new tools appear: `ingest_document`, `query`, `list_documents`.

---

## 7. Day-2 operations

```bash
# Tail logs
docker compose -f docker-compose.prod.yml logs -f

# Restart just the API after pulling code
git pull
./deploy/deploy.sh

# Stop everything
docker compose -f docker-compose.prod.yml down

# Rotate Postgres password — edit .env, then:
docker compose -f docker-compose.prod.yml up -d --force-recreate postgres api
```

### Backups

```bash
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U medrag medrag | gzip > medrag-$(date +%F).sql.gz
```

---

## 8. Going from MOCK → real LLMs

The deploy ships in **mock mode** (the `mock-dev` API keys make the in-memory
vector store and canned LLM responses kick in). To flip to production:

1. Edit `.env` and set real values for `PINECONE_API_KEY`, `ANTHROPIC_API_KEY`,
   `OPENAI_API_KEY`.
2. Replace the imports in `app/routers/demo.py` and `app/mcp_server.py` from
   `mock_vector_store` / `mock_llm` to your real implementations under
   `app/ingestion/pipeline.py` and `app/rag/`.
3. `./deploy/deploy.sh`.

---

## 9. Cost expectation

| Item                       | ~ Monthly USD |
| -------------------------- | ------------- |
| `t3.small`, 730 h on-demand | ~$15          |
| 20 GB gp3                  | ~$2           |
| Public IPv4 (fixed)        | ~$3.60        |
| sslip.io / Let's Encrypt   | $0            |
| **Total**                  | **~$20**      |

Drop to a Reserved Instance or Savings Plan to halve the EC2 line.

---

## 10. Troubleshooting

| Symptom                                        | Fix                                                                 |
| ---------------------------------------------- | ------------------------------------------------------------------- |
| `502 Bad Gateway` from Caddy                   | `docker compose ... logs api` — usually startup error in FastAPI    |
| Cert never issues, Caddy logs show `tls challenge` errors | Confirm port 80 + 443 are open in your security group        |
| `out of memory` during build                   | Resize to `t3.small` or larger                                      |
| MCP client doesn't see tools                   | Hit `/mcp/info` — confirm the `mcp` package is installed in the image |
| Web demo shows `MOCK MODE — demo` badge        | Expected with placeholder API keys; set real ones in `.env`         |
