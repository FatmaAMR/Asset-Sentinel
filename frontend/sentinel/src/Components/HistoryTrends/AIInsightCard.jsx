export default function AIInsightCard() {
  return (
    <div className="bg-gradient-to-br from-primary to-purple-800 p-6 rounded-2xl text-white shadow-xl">
      <div className="flex items-center gap-2 mb-4">
        <span className="material-icons-round text-yellow-300">
          auto_awesome
        </span>
        <span className="text-xs font-bold uppercase tracking-widest opacity-90">
          Sentinel AI Insight
        </span>
      </div>

      <p className="text-sm leading-relaxed mb-4 opacity-95">
        "Vibration peaks in Asset{" "}
        <span className="font-bold underline">#RT-902</span> correlate with a
        15% increase in temperature. Recommend inspection of bearing housing
        within 48 hours."
      </p>

      <button className="text-xs font-semibold bg-white/20 hover:bg-white/30 px-3 py-2 rounded-lg transition-colors w-full">
        View Diagnostic Details
      </button>
    </div>
  );
}
