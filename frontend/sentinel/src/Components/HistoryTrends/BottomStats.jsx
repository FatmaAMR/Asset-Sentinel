export default function BottomStats() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="bg-white dark:bg-[#1E293B] p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <span className="text-slate-500 dark:text-slate-400 text-sm font-medium">
            Avg. MTBF
          </span>
          <span className="material-icons-round text-primary/40">timer</span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold">482 hrs</span>
          <span className="text-emerald-500 text-xs font-bold">+12%</span>
        </div>
      </div>

      <div className="bg-white dark:bg-[#1E293B] p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <span className="text-slate-500 dark:text-slate-400 text-sm font-medium">
            Downtime Reduction
          </span>
          <span className="material-icons-round text-primary/40">
            trending_down
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold">34.2%</span>
          <span className="text-emerald-500 text-xs font-bold">
            Monthly Goal Met
          </span>
        </div>
      </div>

      <div className="bg-white dark:bg-[#1E293B] p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <span className="text-slate-500 dark:text-slate-400 text-sm font-medium">
            Critical Alerts
          </span>
          <span className="material-icons-round text-red-400/60">
            error_outline
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold">03</span>
          <span className="text-slate-500 dark:text-slate-400 text-xs font-medium">
            Active now
          </span>
        </div>
      </div>
    </div>
  );
}
