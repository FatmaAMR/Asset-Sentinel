export default function ContextExplorer() {
  return (
    <section className="bg-primary text-white rounded-[2.5rem] p-8 h-full relative overflow-hidden shadow-2xl shadow-primary/20">
      <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16 blur-2xl" />

      <div className="relative z-10 flex flex-col h-full">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
            <span className="material-symbols-rounded">hub</span>
          </div>
          <h3 className="text-2xl font-display font-bold">Context Explorer</h3>
        </div>

        <p className="text-white/80 text-sm mb-8">
          Visualizing how the RAG engine chunks and indexes technical
          documentation for local inference.
        </p>

        <div className="space-y-4 mb-8">
          <div className="bg-white/10 p-4 rounded-2xl border border-white/20">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] font-bold uppercase tracking-widest opacity-60">
                Chunk ID: #4421
              </span>
              <span className="text-[10px] font-bold bg-accent text-slate-900 px-2 py-0.5 rounded">
                High Relevance
              </span>
            </div>

            <div className="space-y-1.5">
              <div className="h-2 bg-white/30 rounded-full w-full" />
              <div className="h-2 bg-white/30 rounded-full w-[90%]" />
              <div className="h-2 bg-white/30 rounded-full w-[95%]" />
              <div className="h-2 bg-white/30 rounded-full w-[60%]" />
            </div>

            <div className="mt-4 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-accent" />
              <span className="text-xs italic opacity-80">
                Vector: [0.892, 0.221, -0.44...]
              </span>
            </div>
          </div>

          <div className="bg-white/5 p-4 rounded-2xl border border-white/10">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] font-bold uppercase tracking-widest opacity-60">
                Chunk ID: #4422
              </span>
            </div>
            <div className="space-y-1.5">
              <div className="h-2 bg-white/20 rounded-full w-full" />
              <div className="h-2 bg-white/20 rounded-full w-[80%]" />
            </div>
          </div>

          <div className="flex justify-center -space-x-2">
            <div className="w-8 h-8 rounded-full bg-white/20 border-2 border-primary flex items-center justify-center text-[10px]">
              9+
            </div>
            <div className="w-8 h-8 rounded-full bg-white/30 border-2 border-primary" />
            <div className="w-8 h-8 rounded-full bg-white/40 border-2 border-primary" />
          </div>
        </div>

        <div className="mt-auto">
          <div className="bg-white rounded-[1.5rem] p-6 text-slate-900">
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
      </div>
    </section>
  );
}
