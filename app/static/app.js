const $ = (id) => document.getElementById(id);
const apiBase = "";

async function call(path, opts = {}) {
  const res = await fetch(apiBase + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  const text = await res.text();
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    body = text;
  }
  return { ok: res.ok, status: res.status, body };
}

function show(el, payload) {
  el.textContent = typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
}

function appendMessage(role, text) {
  const log = $("chat-log");
  const msg = document.createElement("div");
  msg.className = `msg ${role}`;
  const roleEl = document.createElement("div");
  roleEl.className = "msg-role";
  roleEl.textContent = role;
  const content = document.createElement("div");
  content.className = "msg-content";
  content.textContent = text;
  msg.appendChild(roleEl);
  msg.appendChild(content);
  log.appendChild(msg);
  log.scrollTop = log.scrollHeight;
}

function setLoading(state) {
  $("loading-indicator").classList.toggle("hidden", !state);
  $("query-btn").disabled = state;
}

function humanError(r, fallback) {
  if (!r) return fallback;
  if (typeof r.body === "string" && r.body.trim()) return r.body;
  if (r.body?.detail) return r.body.detail;
  return `${fallback} (HTTP ${r.status})`;
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
  badge.textContent = mode === "mock" ? "mock mode" : "live mode";
  badge.style.color = mode === "mock" ? "var(--accent-2)" : "var(--ok)";
}

async function refreshDocs() {
  const r = await call("/api/v1/documents");
  if (!r.ok) {
    show($("docs-out"), humanError(r, "Could not load document library."));
    return;
  }
  show($("docs-out"), r.body);
}

async function ingest() {
  const btn = $("ingest-btn");
  btn.disabled = true;
  const title = $("doc-title").value.trim() || "Untitled";
  const content = $("doc-content").value.trim();
  if (!content) {
    show($("ingest-out"), "Provide content before ingesting.");
    btn.disabled = false;
    return;
  }

  const url = `/api/v1/ingest?title=${encodeURIComponent(title)}&content=${encodeURIComponent(content)}`;
  const r = await call(url, { method: "POST" });
  if (!r.ok) {
    show($("ingest-out"), humanError(r, "Ingestion failed."));
  } else {
    show($("ingest-out"), r.body);
    appendMessage("assistant", `Document "${title}" ingested. Ask a question to test retrieval.`);
    await refreshDocs();
  }
  btn.disabled = false;
}

function formatAssistantReply(result) {
  const answer = result?.response?.response ?? "(No response text)";
  const citations = result?.response?.citations ?? [];
  const top = result?.retrieved_docs_count ?? result?.retrieved_docs?.length ?? 0;
  const citeText = citations.length ? `\n\nCitations: ${citations.join(", ")}` : "\n\nCitations: none";
  return `${answer}\n\nRetrieved docs: ${top}${citeText}`;
}

async function query() {
  const q = $("query-input").value.trim();
  if (!q) {
    show($("query-out"), "Enter a question.");
    return;
  }

  appendMessage("user", q);
  setLoading(true);

  const r = await call(`/api/v1/query?query=${encodeURIComponent(q)}`, { method: "POST" });
  if (!r.ok) {
    const err = humanError(r, "Query failed.");
    appendMessage("assistant", `Error: ${err}`);
    show($("query-out"), err);
  } else {
    appendMessage("assistant", formatAssistantReply(r.body));
    show($("query-out"), r.body);
  }

  setLoading(false);
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
  $("query-input").addEventListener("keydown", (event) => {
    if (event.key === "Enter") query();
  });

  refreshHealth();
  refreshDocs();
  renderMcpConfig();
});
