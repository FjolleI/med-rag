#!/usr/bin/env bash
# Build & (re)launch the production stack on the current host.
# Run from the repo root:  ./deploy/deploy.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "✗ .env missing. Run:"
  echo "    cp .env.prod.example .env  &&  \$EDITOR .env"
  exit 1
fi

set -a; source .env; set +a

if [[ "${DOMAIN:-}" == "CHANGE-ME.sslip.io" || -z "${DOMAIN:-}" ]]; then
  echo "✗ DOMAIN is unset in .env."
  echo "  Quickest free option:  PUBLIC_IP=\$(curl -s ifconfig.me); echo \"DOMAIN=\${PUBLIC_IP//./-}.sslip.io\""
  exit 1
fi

if [[ "${JWT_SECRET_KEY:-}" == CHANGE-ME* || ${#JWT_SECRET_KEY} -lt 32 ]]; then
  echo "✗ JWT_SECRET_KEY must be set to a strong secret (min 32 chars), not a placeholder."
  echo "  Example:  JWT_SECRET_KEY=\$(openssl rand -base64 32)"
  exit 1
fi

echo "──> Pulling latest images"
docker compose -f docker-compose.prod.yml pull --ignore-buildable || true

echo "──> Building API image"
docker compose -f docker-compose.prod.yml build api

echo "──> Starting stack (DOMAIN=$DOMAIN)"
docker compose -f docker-compose.prod.yml up -d

echo
echo "──> Waiting for health check…"
for i in {1..30}; do
  if curl -fsS "http://localhost:8000/health" >/dev/null 2>&1; then
    echo "✓ API healthy"
    break
  fi
  sleep 2
done

echo
echo "──> Status"
docker compose -f docker-compose.prod.yml ps

echo
echo "✓ Deploy complete."
echo "   Landing page :  https://$DOMAIN"
echo "   API docs     :  https://$DOMAIN/docs"
echo "   MCP endpoint :  https://$DOMAIN/mcp"
echo "   MCP info     :  https://$DOMAIN/mcp/info"
echo "   Health       :  https://$DOMAIN/health"
echo
echo "First HTTPS request may take 10–30 s while Caddy obtains a Let's Encrypt cert."
