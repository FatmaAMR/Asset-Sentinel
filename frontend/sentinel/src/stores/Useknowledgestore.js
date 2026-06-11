import { create } from "zustand";

const BASE = "http://localhost:8002";

export const useKnowledgeStore = create((set, get) => ({
  // --- ingest ---
  isIngesting: false,
  ingestResult: null,
  ingestError: null,

  ingest: async (file) => {
    set({ isIngesting: true, ingestResult: null, ingestError: null });
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${BASE}/rag/ingest`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) throw new Error(`Ingest failed: ${res.status}`);
      const data = await res.json();
      set({ isIngesting: false, ingestResult: data });

      get().fetchStatus();
      get().fetchChunks();
    } catch (err) {
      set({ isIngesting: false, ingestError: err.message });
    }
  },

  resetIngest: () => set({ ingestResult: null, ingestError: null }),

  // --- status (GET /rag/status) ---
  totalChunks: null,
  isReady: false,
  statusLoading: false,

  fetchStatus: async () => {
    set({ statusLoading: true });
    try {
      const res = await fetch(`${BASE}/rag/status`);
      if (!res.ok) throw new Error(`Status failed: ${res.status}`);
      const data = await res.json();

      set({
        statusLoading: false,
        totalChunks: data.total_chunks ?? data.chunks ?? null,
        isReady: data.status === "ready" || data.status === "ok",
      });
    } catch {
      set({ statusLoading: false });
    }
  },

  // --- chunks (GET /rag/chunks?collection=...) ---
  chunks: [],
  chunksLoading: false,
  chunksError: null,
  uniqueSources: [],

  fetchChunks: async (collection = "maintenance_manuals") => {
    set({ chunksLoading: true, chunksError: null });
    try {
      const res = await fetch(`${BASE}/rag/chunks?collection=${collection}`);
      if (!res.ok) throw new Error(`Chunks failed: ${res.status}`);
      const data = await res.json();
      const chunks = Array.isArray(data) ? data : (data.chunks ?? []);

      // Extract unique PDF source filenames
      const uniqueSources = [...new Set(chunks.map((c) => c.source).filter(Boolean))];

      set({
        chunksLoading: false,
        chunks,
        uniqueSources,
      });
    } catch (err) {
      set({ chunksLoading: false, chunksError: err.message, uniqueSources: [] });
    }
  },

  // --- collections (GET /rag/collections) ---
  collections: [],
  collectionsLoading: false,

  fetchCollections: async () => {
    set({ collectionsLoading: true });
    try {
      const res = await fetch(`${BASE}/rag/collections`);
      if (!res.ok) throw new Error(`Collections failed: ${res.status}`);
      const data = await res.json();
      set({
        collectionsLoading: false,
        collections: Array.isArray(data) ? data : (data.collections ?? []),
      });
    } catch {
      set({ collectionsLoading: false });
    }
  },
}));