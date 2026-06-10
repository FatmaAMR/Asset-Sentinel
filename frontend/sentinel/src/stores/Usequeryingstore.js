import { create } from "zustand";

const QUERYING_SERVICE_URL = "http://localhost:8000";

const QUICK_ACTIONS = [
  {
    label: "Compare with 2022 overhaul logs",
    question: "Compare current bearing vibration levels with the 2022 overhaul maintenance logs for asset TRB-9402",
  },
  {
    label: "Show vibration spectrogram",
    question: "Show the vibration frequency data for TRB-9402 from the last 24 hours",
  },
  {
    label: "Estimate MTBF",
    question: "Estimate mean time between failures for Bearing #4 on asset TRB-9402 based on historical maintenance data",
  },
];

export const useQueryingStore = create((set, get) => ({
  // State
  question: "",
  isLoading: false,
  error: null,
  result: null,           // { question, sql, results, status }
  history: [],            // past query results
  quickActions: QUICK_ACTIONS,

  // Actions
  setQuestion: (question) => set({ question }),

  clearResult: () => set({ result: null, error: null }),

  ask: async (questionOverride) => {
    const question = questionOverride ?? get().question;
    if (!question.trim()) return;

    set({ isLoading: true, error: null, result: null, question: "" });

    try {
      const res = await fetch(
        `${QUERYING_SERVICE_URL}/ask?question=${encodeURIComponent(question)}`
      );

      if (!res.ok) {
        throw new Error(`Service responded with ${res.status}`);
      }

      const data = await res.json();

      if (data.status === "db_error") {
        set({
          isLoading: false,
          error: data.error || "Database error occurred.",
          result: { question, sql: data.sql, results: [], status: "db_error" },
        });
        return;
      }

      const newResult = {
        question,
        sql: data.sql,
        results: data.results ?? [],
        status: data.status,
      };

      set((state) => ({
        isLoading: false,
        result: newResult,
        history: [newResult, ...state.history].slice(0, 20),
      }));
    } catch (err) {
      set({
        isLoading: false,
        error: err.message || "Querying service unreachable.",
      });
    }
  },
}));