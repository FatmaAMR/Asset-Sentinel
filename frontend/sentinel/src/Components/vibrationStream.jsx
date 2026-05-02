export default function VibrationStream() {
  return (
    <section className="bg-slate-900 rounded-[2.5rem] p-8 text-white relative overflow-hidden mt-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <span className="w-3 h-3 bg-failure rounded-full animate-pulse" />
            Live Vibration Stream
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Real-time spectral analysis for Turbine Unit 04-B
          </p>
        </div>
        <span className="bg-slate-800 text-slate-300 text-[10px] px-3 py-1.5 rounded-full border border-slate-700">
          60FPS LOW LATENCY
        </span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-4">
            Time Domain (Velocity mm/s)
          </p>
          <div className="h-40 flex items-end gap-1">
            <div className="flex-1 bg-primary/40 rounded-t-sm" style={{ height: "30%" }} />
            <div className="flex-1 bg-primary/60 rounded-t-sm" style={{ height: "45%" }} />
            <div className="flex-1 bg-primary/80 rounded-t-sm" style={{ height: "60%" }} />
            <div className="flex-1 bg-primary rounded-t-sm"    style={{ height: "85%" }} />
            <div className="flex-1 bg-primary/70 rounded-t-sm" style={{ height: "40%" }} />
            <div className="flex-1 bg-primary/50 rounded-t-sm" style={{ height: "25%" }} />
            <div className="flex-1 bg-primary/90 rounded-t-sm" style={{ height: "70%" }} />
            <div className="flex-1 bg-primary rounded-t-sm"    style={{ height: "95%" }} />
            <div className="flex-1 bg-primary/60 rounded-t-sm" style={{ height: "50%" }} />
            <div className="flex-1 bg-primary/30 rounded-t-sm" style={{ height: "20%" }} />
            <div className="flex-1 bg-primary/80 rounded-t-sm" style={{ height: "75%" }} />
            <div className="flex-1 bg-primary/40 rounded-t-sm" style={{ height: "35%" }} />
            <div className="flex-1 bg-primary/60 rounded-t-sm" style={{ height: "55%" }} />
            <div className="flex-1 bg-primary rounded-t-sm"    style={{ height: "90%" }} />
            <div className="flex-1 bg-primary/70 rounded-t-sm" style={{ height: "45%" }} />
          </div>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-4">
            FFT Spectrum (Frequency Hz)
          </p>
          <div className="h-40 flex items-end gap-1">
            <div className="flex-1 bg-warning/40 rounded-t-sm" style={{ height: "10%" }} />
            <div className="flex-1 bg-warning/40 rounded-t-sm" style={{ height: "15%" }} />
            <div className="flex-1 bg-warning/80 rounded-t-sm" style={{ height: "80%" }} />
            <div className="flex-1 bg-warning/40 rounded-t-sm" style={{ height: "12%" }} />
            <div className="flex-1 bg-warning/40 rounded-t-sm" style={{ height: "10%" }} />
            <div className="flex-1 bg-warning/40 rounded-t-sm" style={{ height: "18%" }} />
            <div className="flex-1 bg-warning/60 rounded-t-sm" style={{ height: "40%" }} />
            <div className="flex-1 bg-warning/40 rounded-t-sm" style={{ height: "15%" }} />
            <div className="flex-1 bg-warning/40 rounded-t-sm" style={{ height: "12%" }} />
            <div className="flex-1 bg-warning/90 rounded-t-sm" style={{ height: "95%" }} />
            <div className="flex-1 bg-warning/40 rounded-t-sm" style={{ height: "15%" }} />
            <div className="flex-1 bg-warning/40 rounded-t-sm" style={{ height: "10%" }} />
            <div className="flex-1 bg-warning/40 rounded-t-sm" style={{ height: "25%" }} />
            <div className="flex-1 bg-warning/40 rounded-t-sm" style={{ height: "15%" }} />
            <div className="flex-1 bg-warning/40 rounded-t-sm" style={{ height: "8%"  }} />
          </div>
        </div>

      </div>
      <div className="mt-8 pt-8 border-t border-slate-800 flex flex-wrap gap-8">
        <div>
          <span className="block text-slate-500 text-[10px] font-bold uppercase mb-1">Crest Factor</span>
          <span className="text-xl font-mono">1.42</span>
        </div>
        <div>
          <span className="block text-slate-500 text-[10px] font-bold uppercase mb-1">Kurtosis</span>
          <span className="text-xl font-mono">3.05</span>
        </div>
        <div>
          <span className="block text-slate-500 text-[10px] font-bold uppercase mb-1">Temperature</span>
          <span className="text-xl font-mono text-normal">54.2°C</span>
        </div>
        <div className="ml-auto flex items-center gap-4">
          <span className="text-xs text-slate-400">AI analysis running on local edge...</span>
          <button className="bg-white text-slate-900 px-6 py-2 rounded-xl text-xs font-bold hover:bg-primary hover:text-white transition-all">
            Capture Snapshot
          </button>
        </div>
      </div>

    </section>
  );
}