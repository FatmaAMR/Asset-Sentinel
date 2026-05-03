export default function FiltersSidebar() {
  return (
    <div className="bg-white dark:bg-[#1E293B] p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-semibold text-lg">Filters</h3>
        <button className="text-sm text-primary font-medium">Reset</button>
      </div>

      <div className="space-y-6">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
            Date Range
          </label>
          <select className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-sm focus:ring-primary focus:border-primary">
            <option>Last 30 Days</option>
            <option>Last 90 Days</option>
            <option>Last 6 Months</option>
            <option>Custom Range</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
            Severity
          </label>

          <div className="space-y-2">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                defaultChecked
                className="rounded border-slate-300 text-primary focus:ring-primary h-4 w-4"
                type="checkbox"
              />
              <span className="text-sm text-red-500 font-medium">Critical</span>
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                defaultChecked
                className="rounded border-slate-300 text-primary focus:ring-primary h-4 w-4"
                type="checkbox"
              />
              <span className="text-sm text-amber-500 font-medium">
                Warning
              </span>
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                className="rounded border-slate-300 text-primary focus:ring-primary h-4 w-4"
                type="checkbox"
              />
              <span className="text-sm text-emerald-500 font-medium">
                Healthy
              </span>
            </label>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
            Asset Category
          </label>

          <div className="flex flex-wrap gap-2">
            <button className="px-3 py-1.5 rounded-full text-xs font-medium bg-primary text-white">
              All Assets
            </button>
            <button className="px-3 py-1.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700">
              Turbines
            </button>
            <button className="px-3 py-1.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700">
              Conveyors
            </button>
            <button className="px-3 py-1.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700">
              Motors
            </button>
          </div>
        </div>

        <button className="w-full bg-primary hover:bg-primary/90 text-white font-semibold py-3 rounded-xl transition-all shadow-lg shadow-primary/20 flex items-center justify-center gap-2 mt-4">
          <span className="material-icons-round text-sm">filter_list</span>
          Apply Filters
        </button>
      </div>
    </div>
  );
}
