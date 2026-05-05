import { useState } from "react";
import useQueryingStore from "../../stores/queringStore";

export default function ContextExplorer() {
  const {
    ask,
    answer,
    sources,
    question,
    history,
    loading,
    error,
    clearAnswer,
  } = useQueryingStore();
  const [input, setInput] = useState("");

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    await ask(input.trim());
    setInput("");
  };

  return (
    <section className="bg-primary text-white rounded-[2.5rem] p-8 h-full relative overflow-hidden shadow-2xl shadow-primary/20">
      <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16 blur-2xl" />

      <div className="relative z-10 flex flex-col h-full gap-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
            <span className="material-symbols-rounded">hub</span>
          </div>
          <h3 className="text-2xl font-display font-bold">Context Explorer</h3>
        </div>

        <p className="text-white/80 text-sm">
          Ask the RAG engine a question about your indexed technical
          documentation.
        </p>

        {/* Input */}
        <form onSubmit={handleAsk} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="e.g. What is the bearing torque spec?"
            disabled={loading}
            className="flex-1 bg-white/10 border border-white/20 text-white placeholder-white/40 text-sm rounded-2xl px-4 py-2.5 outline-none focus:border-white/50 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-white text-primary font-bold px-4 py-2.5 rounded-2xl hover:bg-white/90 transition disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <span className="material-symbols-rounded text-base">
              {loading ? "hourglass_top" : "send"}
            </span>
          </button>
        </form>

        {/* Answer */}
        {(answer || error) && (
          <div className="bg-white/10 border border-white/20 rounded-2xl p-4 text-sm space-y-3">
            {error ? (
              <p className="text-red-300 flex items-center gap-2">
                <span className="material-symbols-rounded text-base">
                  error
                </span>
                {error}
              </p>
            ) : (
              <>
                <p className="text-white/60 text-[11px] uppercase tracking-widest font-bold">
                  Q: {question}
                </p>
                <p className="text-white leading-relaxed">{answer}</p>

                {sources?.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-1 border-t border-white/10">
                    {sources.map((s, i) => (
                      <span
                        key={i}
                        className="text-[10px] font-bold bg-white/10 border border-white/20 px-2 py-0.5 rounded-full flex items-center gap-1"
                      >
                        <span className="material-symbols-rounded text-[10px]">
                          description
                        </span>
                        {typeof s === "string"
                          ? s
                          : (s.source ?? s.file ?? `Source ${i + 1}`)}
                      </span>
                    ))}
                  </div>
                )}

                <button
                  onClick={clearAnswer}
                  className="text-white/40 hover:text-white/80 text-[11px] flex items-center gap-1 transition"
                >
                  <span className="material-symbols-rounded text-[11px]">
                    close
                  </span>
                  Clear
                </button>
              </>
            )}
          </div>
        )}

        {/* Recent history */}
        {history.length > 0 && !answer && (
          <div className="space-y-2 overflow-y-auto max-h-40">
            <p className="text-white/50 text-[10px] uppercase tracking-widest font-bold">
              Recent
            </p>
            {history.slice(0, 3).map((h) => (
              <div
                key={h.id}
                className="bg-white/5 border border-white/10 rounded-xl p-3 text-xs"
              >
                <p className="text-white/60 mb-1">Q: {h.question}</p>
                <p className="text-white line-clamp-2">{h.answer}</p>
              </div>
            ))}
          </div>
        )}

        {/* Bottom card — live indexing efficiency */}
        <div className="mt-auto bg-white rounded-[1.5rem] p-6 text-slate-900">
          <h4 className="font-bold mb-1">Indexing Efficiency</h4>
          <div className="flex items-center justify-between mb-4">
            <span className="text-3xl font-display font-extrabold text-primary">
              98.4%
            </span>
            <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">
              +2.1%
            </span>
          </div>
          <p className="text-[11px] text-slate-500 font-medium">
            Optimized for GPT4-All and Llama-3 local instances.
          </p>
        </div>
      </div>
    </section>
  );
}
