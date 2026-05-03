export default function LlmModels() {
  return (
    <section>
      <div className="flex items-center justify-between mb-6 px-2">
        <h3 className="text-xl font-bold">Local LLM Models</h3>
        <span className="text-sm font-medium text-primary bg-primary/10 px-3 py-1 rounded-full">
          3 Models Available
        </span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-cards-light p-6 rounded-3xl border border-slate-200 shadow-sm hover:shadow-xl transition-all duration-300">
          <div className="flex items-start justify-between mb-6">
            <div className="w-14 h-14 bg-indigo-50 rounded-2xl flex items-center justify-center text-indigo-600">
              <span className="material-icons-round text-3xl">psychology</span>
            </div>
            <span className="px-3 py-1 bg-green-100 text-green-600 rounded-full text-xs font-bold uppercase tracking-wider">
              Active
            </span>
          </div>
          <h4 className="text-xl font-bold mb-2">Qwen-2.5-7B</h4>
          <p className="text-slate-500 text-sm mb-6 leading-relaxed">
            High precision diagnostics optimized for mechanical telemetry. Best for multi-step reasoning.
          </p>
          <div className="flex items-center gap-4 mb-6">
            <div className="text-xs text-slate-400">
              <span className="block font-bold text-slate-900">7.2B</span>
              Params
            </div>
            <div className="text-xs text-slate-400">
              <span className="block font-bold text-slate-900">4.8GB</span>
              VRAM
            </div>
            <div className="text-xs text-slate-400">
              <span className="block font-bold text-slate-900">128k</span>
              Context
            </div>
          </div>
          <button className="w-full py-3 bg-slate-100 text-slate-400 font-bold rounded-2xl cursor-not-allowed">
            Currently Running
          </button>
        </div>
        <div className="bg-cards-light p-6 rounded-3xl border border-slate-200 shadow-sm hover:shadow-xl transition-all duration-300">
          <div className="flex items-start justify-between mb-6">
            <div className="w-14 h-14 bg-orange-50 rounded-2xl flex items-center justify-center text-orange-600">
              <span className="material-icons-round text-3xl">auto_awesome</span>
            </div>
            <span className="px-3 py-1 bg-slate-100 text-slate-500 rounded-full text-xs font-bold uppercase tracking-wider">
              Ready
            </span>
          </div>
          <h4 className="text-xl font-bold mb-2">Llama-3.2-3B</h4>
          <p className="text-slate-500 text-sm mb-6 leading-relaxed">
            Lightweight edge-optimized model for rapid alerting and basic maintenance triage.
          </p>
          <div className="flex items-center gap-4 mb-6">
            <div className="text-xs text-slate-400">
              <span className="block font-bold text-slate-900">3.1B</span>
              Params
            </div>
            <div className="text-xs text-slate-400">
              <span className="block font-bold text-slate-900">2.2GB</span>
              VRAM
            </div>
            <div className="text-xs text-slate-400">
              <span className="block font-bold text-slate-900">32k</span>
              Context
            </div>
          </div>
          <button className="w-full py-3 bg-primary text-white font-bold rounded-2xl hover:opacity-90 transition-all shadow-lg shadow-primary/20">
            Set Active
          </button>
        </div>

      </div>
    </section>
  );
}