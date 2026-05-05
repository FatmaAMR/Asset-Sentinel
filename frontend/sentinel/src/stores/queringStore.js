import { create } from "zustand";
import { askQuestion, ingestPDF, fetchStatus } from "../services/ragApi";

const useQueryingStore = create((set) => ({
  // ── State ──────────────────────────────────────────────
  answer: null,
  question: "",
  sources: [],
  history: [],

  ingestResult: null, // { status, chunks_added, total_chunks }

  totalChunks: null,
  isReady: false,

  loading: false,
  error: null,

  // ── Ask ────────────────────────────────────────────────
  ask: async (question, top_k = 5) => {
    set({ loading: true, error: null, answer: null, sources: [], question });
    try {
      const res = await askQuestion(question, top_k);
      set((state) => ({
        answer: res.answer,
        sources: res.sources ?? [],
        history: [
          {
            id: Date.now(),
            question: res.question,
            answer: res.answer,
            sources: res.sources ?? [],
          },
          ...state.history,
        ],
      }));
    } catch (err) {
      set({ error: err.message });
    } finally {
      set({ loading: false });
    }
  },

  // ── Ingest ─────────────────────────────────────────────
  ingest: async (file) => {
    set({ loading: true, error: null, ingestResult: null });
    try {
      const res = await ingestPDF(file);
      set({ ingestResult: res, totalChunks: res.total_chunks ?? null });
    } catch (err) {
      set({ error: err.message });
    } finally {
      set({ loading: false });
    }
  },

  // ── Status ─────────────────────────────────────────────
  fetchStatus: async () => {
    set({ loading: true, error: null });
    try {
      const res = await fetchStatus();
      set({
        isReady: res.status === "ready",
        totalChunks: res.total_chunks ?? null,
      });
    } catch (err) {
      set({ error: err.message });
    } finally {
      set({ loading: false });
    }
  },

  // ── Helpers ────────────────────────────────────────────
  clearAnswer: () =>
    set({ answer: null, question: "", sources: [], error: null }),
  clearHistory: () => set({ history: [] }),
  resetIngest: () => set({ ingestResult: null, error: null }),
}));

export default useQueryingStore;
