export default function AppFooter() {
  return (
    <footer className="h-10 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-card-dark px-6 flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-slate-400">
      <div className="flex gap-4">
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-green-500" /> System Ready
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-primary" /> LLM Online
        </span>
      </div>
      <div>Asset ID: TRB-9402-B-SENTINEL • Session: 4,921</div>
    </footer>
  );
}
