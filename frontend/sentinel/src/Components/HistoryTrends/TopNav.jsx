export default function TopNav({ dark, onToggleDark }) {
  return (
    <nav className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-[#1E293B] sticky top-0 z-50">
      <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="material-icons-round text-white text-xl">
                insights
              </span>
            </div>
            <span className="text-xl font-bold tracking-tight">SENTINEL</span>
          </div>

          <div className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-500 dark:text-slate-400">
            <a className="hover:text-primary transition-colors" href="#">
              Fleet Health
            </a>
            <a className="text-primary border-b-2 border-primary py-5" href="#">
              History & Trends
            </a>
            <a className="hover:text-primary transition-colors" href="#">
              Diagnostics
            </a>
            <a className="hover:text-primary transition-colors" href="#">
              Assets
            </a>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button
            className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 transition-colors"
            onClick={onToggleDark}
            aria-label="toggle dark mode"
            title={dark ? "Light mode" : "Dark mode"}
          >
            <span className="material-icons-round">dark_mode</span>
          </button>

          <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center overflow-hidden">
            <div className="w-full h-full bg-slate-300 dark:bg-slate-600" />
          </div>
        </div>
      </div>
    </nav>
  );
}
