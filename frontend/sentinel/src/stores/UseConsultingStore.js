import { create } from "zustand";

const CONSULTING_SERVICE_URL = "http://localhost:8002";
const NOTIFICATION_SERVICE_URL = "http://localhost:8006";


function parseRecommendations(answer) {

  const sentences = answer
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 20);
  const recKeywords =
    /recommend|should|must|replace|monitor|implement|check|inspect|ensure|avoid/i;
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

export const useConsultingStore = create((set, get) => ({
  // ── State ────────────────────────────────────────────────────────────────
  isLoading: false,
  error: null,
  rawAnswer: null,
  rootCause: null,
  recommendations: [],
  citation: null,
  sources: [],
  confidence: null,

  // Active machine — change this to switch which machine is diagnosed
  machineId: "machine-81",

  // Raw notifications from GET /rag/notifications/{machine_id}
  notifications: [],
  notificationsLoading: false,
  notificationsError: null,

  // ── Setters ──────────────────────────────────────────────────────────────

  setMachineId: (id) => set({ machineId: id }),

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

  // ── GET /rag/notifications/{machine_id} ──────────────────────────────────
  // Polls the notification service for the latest diagnosis results.
  // Call this on mount and on a polling interval (e.g. every 10 s).
  fetchNotifications: async (machineId, limit = 10) => {
    const id = machineId || get().machineId;
    set({ notificationsLoading: true, notificationsError: null });

    try {
      const res = await fetch(
        `${CONSULTING_SERVICE_URL}/rag/notifications/${id}?limit=${limit}`
      );
      if (!res.ok)
        throw new Error(`Notification service responded with ${res.status}`);

      const data = await res.json();
      // shape: { machine_id, count, notifications: [...] }
      const messages = data.notifications || data.messages || [];

      // Use the latest message to populate the diagnosis panel
      if (messages.length > 0) {
        const latest = messages[0]; // newest first
        const answer = latest.fault_cause || latest.extracted_reason || "";
        set({
          notifications: messages,
          notificationsLoading: false,
          rawAnswer: answer,
          rootCause: latest.extracted_reason || answer,
          recommendations: parseRecommendations(answer),
          citation: null,
          sources: [],
          confidence: null,
          error: null,
        });
      } else {
        set({ notifications: [], notificationsLoading: false });
      }
    } catch (err) {
      set({
        notificationsLoading: false,
        notificationsError: err.message || "Notification service unreachable.",
      });
    }
  },

  // ── POST /rag/ask ────────────────────────────────────────────────────────
  askConsulting: async (question, topK = 4) => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch(`${CONSULTING_SERVICE_URL}/rag/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, top_k: topK }),
      });
      if (!res.ok)
        throw new Error(`Consulting service responded with ${res.status}`);

      const data = await res.json();
      const answer = data.answer || "";
      const sentences = answer
        .split(/(?<=[.!?])\s+/)
        .map((s) => s.trim())
        .filter(Boolean);
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
      set({ isLoading: false, error: err.message || "Consulting service unreachable." });
    }
  },

  // ── POST /rag/diagnose ───────────────────────────────────────────────────
  diagnose: async (sensorPayload) => {
    set({ isLoading: true, error: null, rawAnswer: null });
    try {
      const res = await fetch(`${CONSULTING_SERVICE_URL}/rag/diagnose`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sensorPayload),
      });
      if (!res.ok)
        throw new Error(`Diagnose endpoint responded with ${res.status}`);

      const data = await res.json();
      const answer = data.fault_cause || data.extracted_reason || "";
      set({
        isLoading: false,
        rawAnswer: answer,
        rootCause: data.extracted_reason || answer,
        recommendations: parseRecommendations(answer),
        citation: parseCitation(data.sources),
        sources: data.sources || [],
        confidence: null,
      });
    } catch (err) {
      set({ isLoading: false, error: err.message || "Diagnose service unreachable." });
    }
  },

  // ── POST /rag/machine-query ──────────────────────────────────────────────
  machineQuery: async (query, machineId) => {
    const id = machineId || get().machineId;
    set({ isLoading: true, error: null });
    try {
      const payload = {
        machine_id:     id,
        label:          query,
        rul:            0,
        window_sliding: [],
        message_id:     crypto.randomUUID(),
        timestamp:      Date.now() / 1000,
        top_k:          5,
      };
      const res = await fetch(`${CONSULTING_SERVICE_URL}/rag/machine-query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok)
        throw new Error(`Machine query responded with ${res.status}`);

      const data = await res.json();
      const answer = data.best_reason || "";
      set({
        isLoading: false,
        rawAnswer: answer,
        rootCause: answer,
        recommendations:
          data.matches?.map((m) => m.stored_reason).filter(Boolean) || [],
        citation: data.matches?.[0]
          ? {
              title: `Best match — distance: ${data.matches[0].distance?.toFixed(4)}`,
              text: data.matches[0].text_preview,
            }
          : null,
        sources:
          data.matches?.map((m) => ({
            file: m.source,
            page: 0,
            content: m.full_text,
          })) || [],
      });
    } catch (err) {
      set({ isLoading: false, error: err.message || "Machine query unreachable." });
    }
  },
}));
