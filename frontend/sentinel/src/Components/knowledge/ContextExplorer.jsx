import { useEffect, useState } from "react";
import { useKnowledgeStore } from "../../stores/useKnowledgeStore";
import { useConsultingStore } from "../../stores/useConsultingStore";

export default function ContextExplorer() {
  const {
    fetchStatus,
    fetchCollections,
    fetchChunks,
    totalChunks,
    isReady,
    collections,
    collectionsLoading,
    chunks,
    chunksLoading,
    uniqueSources,
  } = useKnowledgeStore();

  const {
    askConsulting,
    isLoading,
    rawAnswer,
    sources,
    error,
    clearDiagnosis,
  } = useConsultingStore();

  const [input, setInput] = useState("");
  const [question, setQuestion] = useState("");
  const [selectedCollection, setSelectedCollection] = useState(null);

  useEffect(() => {
    fetchStatus();
    fetchCollections();
    fetchChunks("maintenance_manuals");
  }, []);

  // When collections load, auto-select first
  useEffect(() => {
    if (collections.length > 0 && !selectedCollection) {
      const first = typeof collections[0] === "string" ? collections[0] : collections[0].name;
      setSelectedCollection(first);
    }
  }, [collections]);

  const handleSelectCollection = (name) => {
    setSelectedCollection(name);
    fetchChunks(name);
  };

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    setQuestion(input.trim());
    await askConsulting(input.trim(), 4);
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
          Visualizing how the RAG engine chunks and indexes technical
          documentation for local inference.
        </p>

        {/* Collection selector pills */}
        {!collectionsLoading && collections.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {collections.map((col) => {
              const name = typeof col === "string" ? col : col.name;
              return (
                <button
                  key={name}
                  onClick={() => handleSelectCollection(name)}
                  className={`text-[10px] font-bold px-3 py-1 rounded-full border transition-all ${
                    selectedCollection === name
                      ? "bg-white text-primary border-white"
                      : "bg-white/10 text-white/70 border-white/20 hover:bg-white/20"
                  }`}
                >
                  {name.replace(/_/g, " ")}
                </button>
              );
            })}
          </div>
        )}

        {/* PDF document cards derived from chunk sources */}
        <div className="space-y-3">
          {chunksLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-white/10 rounded-2xl p-4 animate-pulse">
                  <div className="h-3 bg-white/20 rounded w-1/3 mb-2" />
                  <div className="h-2 bg-white/10 rounded w-full mb-1" />
                  <div className="h-2 bg-white/10 rounded w-3/4" />
                </div>
              ))}
            </div>
          ) : uniqueSources.length === 0 ? (
            <div className="bg-white/10 border border-white/20 rounded-2xl p-4 text-white/50 text-sm text-center">
              No documents indexed yet.
            </div>
          ) : (
            uniqueSources.slice(0, 3).map((source, i) => {
              const sourceChunks = chunks.filter((c) => c.source === source);
              const preview = sourceChunks[0]?.text_preview ?? "";
              return (
                <div key={source} className="bg-white/10 border border-white/20 rounded-2xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-white/80 truncate pr-2 flex items-center gap-1">
                      <span className="material-symbols-rounded text-xs">picture_as_pdf</span>
                      {source}
                    </span>
                    {i === 0 && (
                      <span className="text-[10px] font-bold bg-yellow-400 text-yellow-900 px-2 py-0.5 rounded-full flex-shrink-0">
                        Active
                      </span>
                    )}
                    <span className="text-[10px] font-bold bg-white/20 text-white px-2 py-0.5 rounded-full flex-shrink-0">
                      {sourceChunks.length} chunks
                    </span>
                  </div>
                  <div className="space-y-1 mb-2">
                    <div className="h-1.5 bg-white/30 rounded-full w-full" />
                    <div className="h-1.5 bg-white/20 rounded-full w-4/5" />
                    <div className="h-1.5 bg-white/10 rounded-full w-3/5" />
                  </div>
                  <p className="text-white/60 text-[11px] font-mono leading-relaxed line-clamp-2">
                    <span className="w-2 h-2 rounded-full bg-amber-400 inline-block mr-1" />
                    {preview}
                  </p>
                  <p className="text-white/30 text-[10px] font-mono mt-1">
                    {sourceChunks[0]?.embed_type ?? ""}
                  </p>
                </div>
              );
            })
          )}
        </div>

        {/* Ask input */}
        <form onSubmit={handleAsk} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="e.g. What is the bearing torque spec?"
            disabled={isLoading}
            className="flex-1 bg-white/10 border border-white/20 text-white placeholder-white/40 text-sm rounded-2xl px-4 py-2.5 outline-none focus:border-white/50 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="bg-white text-primary font-bold px-4 py-2.5 rounded-2xl hover:bg-white/90 transition disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <span className="material-symbols-rounded text-base">
              {isLoading ? "hourglass_top" : "send"}
            </span>
          </button>
        </form>

        {/* Answer */}
        {(rawAnswer || error) && (
          <div className="bg-white/10 border border-white/20 rounded-2xl p-4 text-sm space-y-3">
            {error ? (
              <p className="text-red-300 flex items-center gap-2">
                <span className="material-symbols-rounded text-base">error</span>
                {error}
              </p>
            ) : (
              <>
                {question && (
                  <p className="text-white/60 text-[11px] uppercase tracking-widest font-bold">
                    Q: {question}
                  </p>
                )}
                <p className="text-white leading-relaxed">{rawAnswer}</p>

                {sources?.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-1 border-t border-white/10">
                    {sources.map((s, i) => (
                      <span
                        key={i}
                        className="text-[10px] font-bold bg-white/10 border border-white/20 px-2 py-0.5 rounded-full flex items-center gap-1"
                      >
                        <span className="material-symbols-rounded text-[10px]">description</span>
                        {typeof s === "string" ? s : (s.source ?? s.file ?? `Source ${i + 1}`)}
                      </span>
                    ))}
                  </div>
                )}

                <button
                  onClick={() => { clearDiagnosis(); setQuestion(""); }}
                  className="text-white/40 hover:text-white/80 text-[11px] flex items-center gap-1 transition"
                >
                  <span className="material-symbols-rounded text-[11px]">close</span>
                  Clear
                </button>
              </>
            )}
          </div>
        )}

        {/* Bottom card */}
        <div className="mt-auto bg-white rounded-[1.5rem] p-6 text-slate-900">
          <h4 className="font-bold mb-1">Indexing Efficiency</h4>
          <div className="flex items-center justify-between mb-2">
            <span className="text-3xl font-display font-extrabold text-primary">
              98.4%
            </span>
            <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">
              +2.1%
            </span>
          </div>
          {totalChunks != null && (
            <p className="text-[11px] text-slate-500 font-medium mb-1">
              <span className="font-bold text-slate-700">{totalChunks.toLocaleString()}</span> chunks indexed
              {isReady && (
                <span className="ml-2 text-emerald-600 font-bold">● Live</span>
              )}
            </p>
          )}
          <p className="text-[11px] text-slate-500 font-medium">
            Optimized for GPT4-All and Llama-3 local instances.
          </p>
        </div>
      </div>
    </section>
  );
}
