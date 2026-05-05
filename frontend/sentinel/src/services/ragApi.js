/**
 * ragApi.js
 * ─────────────────────────────────────────────
 * Low-level fetch wrappers for the RAG backend.
 * All functions throw on non-2xx responses so the
 * store can handle errors in one place.
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

/**
 * Helper – parses JSON and throws a readable error on failure.
 */
async function handleResponse(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data?.detail ?? `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

// ─── Endpoints ───────────────────────────────────────────────────────────────

/**
 * POST /rag/ask
 * @param {string}  question
 * @param {number}  [top_k=5]
 * @returns {Promise<{ question, answer, sources, intent }>}
 */
export async function askQuestion(question, top_k = 5) {
  const res = await fetch(`${BASE_URL}/rag/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k }),
  });
  return handleResponse(res);
}

/**
 * POST /rag/ingest
 * @param {File} file  – must be a PDF
 * @returns {Promise<{ status, chunks_added, total_chunks }>}
 */
export async function ingestPDF(file) {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${BASE_URL}/rag/ingest`, {
    method: "POST",
    body: form,
    // Do NOT set Content-Type here – browser sets it with boundary automatically
  });
  return handleResponse(res);
}

/**
 * GET /rag/status
 * @returns {Promise<{ status, total_chunks }|{ status, detail }>}
 */
export async function fetchStatus() {
  const res = await fetch(`${BASE_URL}/rag/status`);
  return handleResponse(res);
}
