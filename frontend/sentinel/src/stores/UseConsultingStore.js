import { create } from "zustand";

const CONSULTING_SERVICE_URL = "http://localhost:8002";

// Split answer into sentences and group into recommendations
function parseRecommendations(answer) {
  const sentences = answer
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 20);

  // Look for recommendation-like sentences
  const recKeywords = /recommend|should|must|replace|monitor|implement|check|inspect|ensure|avoid/i;
  const recs = sentences.filter((s) => recKeywords.test(s));
  return recs.length > 0 ? recs.slice(0, 4) : sentences.slice(1, 4);
}

function parseCitation(sources) {
  if (!sources || sources.length === 0) return null;
  const s = sources[0];
  return {
    title: `Citing: ${s.file} — Page ${s.page}`,
    text: s.content?.slice(0, 220) || "",
  };
}

export const useConsultingStore = create((set) => ({
  // State
  isLoading: false,
  error: null,
  rawAnswer: null,       // full answer string from service
  rootCause: null,       // first sentence of answer
  recommendations: [],   // recommendation sentences
  citation: null,        // { title, text } from first source
  sources: [],           // all sources
  confidence: null,      // not returned by service — kept for future

  // Actions
  clearDiagnosis: () =>
    set({
      isLoading: false,
      error: null,
      rawAnswer: null,
      rootCause: null,
      recommendations: [],
      citation: null,
      sources: [],
      confidence: null,
    }),

  askConsulting: async (question, topK = 4) => {
    set({ isLoading: true, error: null });

    try {
      const res = await fetch(`${CONSULTING_SERVICE_URL}/rag/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, top_k: topK }),
      });

      if (!res.ok) throw new Error(`Consulting service responded with ${res.status}`);

      const data = await res.json();
      // data shape: { question, answer, sources: [{file, page, content}], intent }

      const answer = data.answer || "";
      const sentences = answer.split(/(?<=[.!?])\s+/).map((s) => s.trim()).filter(Boolean);

      set({
        isLoading: false,
        rawAnswer: answer,
        rootCause: sentences[0] || answer,
        recommendations: parseRecommendations(answer),
        citation: parseCitation(data.sources),
        sources: data.sources || [],
        confidence: null,
      });
    } catch (err) {
      set({
        isLoading: false,
        error: err.message || "Consulting service unreachable.",
      });
    }
  },
}));
