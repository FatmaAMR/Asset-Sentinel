export default function AssetTopBar() {
  return (
    <div className="px-8 py-4 bg-white dark:bg-card-dark border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
      <div>
        <h1 className="text-xl font-bold flex items-center gap-3">
          Asset #TRB-9402: Gas Turbine B
          <span className="px-2 py-0.5 rounded bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-xs font-bold">
            CRITICAL
          </span>
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Diagnosis session started 08:24 AM • Model: Siemens SGT-800
        </p>
      </div>

      <div className="flex gap-3">
        <a href="history.html">
          <button className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-lg text-sm font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
            <span className="material-symbols-rounded text-lg">history</span>
            History
          </button>
        </a>

        <a href="export_report.html">
          <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg text-sm font-semibold shadow-lg shadow-primary/20 hover:scale-[1.02] transition-transform">
            <span className="material-symbols-rounded text-lg">ios_share</span>
            Export Report
          </button>
        </a>
      </div>
    </div>
  );
}
