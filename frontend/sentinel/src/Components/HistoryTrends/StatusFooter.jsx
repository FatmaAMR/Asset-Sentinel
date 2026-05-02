export default function StatusFooter() {
  return (
    <footer className="mt-12 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-[#1E293B] py-4 px-6">
      <div className="max-w-[1600px] mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-xs font-medium text-slate-500 dark:text-slate-400">
        <div className="flex items-center gap-6">
          <span className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Local LLM: Online
          </span>
          <span className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            Fleet Data: Syncing
          </span>
        </div>

        <p>© 2023 Sentinel Systems. All diagnostics AI-verified.</p>
      </div>
    </footer>
  );
}
