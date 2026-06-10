import { useEffect } from "react";
import { useKnowledgeStore } from "../../stores/useKnowledgeStore";

export default function StatsRow() {
  const { fetchStatus, totalChunks, isReady, statusLoading } = useKnowledgeStore();

  useEffect(() => {
    fetchStatus();
  }, []);

  const displayChunks =
    totalChunks != null
      ? totalChunks.toLocaleString()
      : statusLoading
      ? "…"
      : "—";

  return (
    <section className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-8 py-10 border-t border-slate-200 dark:border-slate-800">
      {/* Live from /rag/status */}
      <div>
        <span className="block text-3xl font-display font-extrabold text-primary mb-1">
          {displayChunks}
        </span>
        <span className="text-sm font-bold text-slate-400 uppercase tracking-widest">
          Total Chunks
        </span>
        {isReady && (
          <span className="mt-1 inline-block text-[10px] font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 px-2 py-0.5 rounded-full">
            Live
          </span>
        )}
      </div>

      {/* Static stats */}
      <div>
        <span className="block text-3xl font-display font-extrabold text-primary mb-1">
          156
        </span>
        <span className="text-sm font-bold text-slate-400 uppercase tracking-widest">
          Library Docs
        </span>
      </div>
      <div>
        <span className="block text-3xl font-display font-extrabold text-primary mb-1">
          2.4ms
        </span>
        <span className="text-sm font-bold text-slate-400 uppercase tracking-widest">
          Retrieval Latency
        </span>
      </div>
      <div>
        <span className="block text-3xl font-display font-extrabold text-primary mb-1">
          0.92
        </span>
        <span className="text-sm font-bold text-slate-400 uppercase tracking-widest">
          Avg. Similarity
        </span>
      </div>
    </section>
  );
}
