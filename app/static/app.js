const $ = (id) => document.getElementById(id);
const apiBase = ""; // same origin

async function call(path, opts = {}) {
  const res = await fetch(apiBase + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  const text = await res.text();
  try { return { ok: res.ok, status: res.status, body: JSON.parse(text) }; }
  catch { return { ok: res.ok, status: res.status, body: text }; }
}

function show(el, payload) {
  el.textContent = typeof payload === "string"
    ? payload
    : JSON.stringify(payload, null, 2);
}

async function refreshHealth() {
  const r = await call("/health");
  const badge = $("mode-badge");
  if (!r.ok) {
    badge.textContent = "offline";
    badge.style.color = "var(--danger)";
    return;
  }
  const mode = r.body.mode || "unknown";
  badge.textContent = mode === "mock" ? "MOCK MODE — demo" : "LIVE";
}

async function refreshDocs() {
  const r = await call("/api/v1/documents");
  show($("docs-out"), r.body);
}

async function ingest() {
  const btn = $("ingest-btn");
  btn.disabled = true;
  const title = $("doc-title").value.trim() || "Untitled";
  const content = $("doc-content").value.trim();
  if (!content) {
    show($("ingest-out"), "⚠ Provide some content to ingest.");
    btn.disabled = false;
    return;
  }
  const url = `/api/v1/ingest?title=${encodeURIComponent(title)}&content=${encodeURIComponent(content)}`;
  const r = await call(url, { method: "POST" });
  show($("ingest-out"), r.body);
  await refreshDocs();
  btn.disabled = false;
}

async function query() {
  const btn = $("query-btn");
  btn.disabled = true;
  const q = $("query-input").value.trim();
  if (!q) {
    show($("query-out"), "⚠ Enter a question.");
    btn.disabled = false;
    return;
  }
  const r = await call(`/api/v1/query?query=${encodeURIComponent(q)}`, { method: "POST" });
  show($("query-out"), r.body);
  btn.disabled = false;
}

function renderMcpConfig() {
  const origin = window.location.origin;
  const cfg = {
    mcpServers: {
      medrag: {
        url: `${origin}/mcp`,
        transport: "streamable-http",
      },
    },
  };
  show($("mcp-config"), cfg);
  $("mcp-info-link").href = `${origin}/mcp/info`;
}

document.addEventListener("DOMContentLoaded", () => {
  $("ingest-btn").addEventListener("click", ingest);
  $("query-btn").addEventListener("click", query);
  $("refresh-docs").addEventListener("click", refreshDocs);
  refreshHealth();
  refreshDocs();
  renderMcpConfig();
});
