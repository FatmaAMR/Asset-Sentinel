export default function KnowledgeFooter() {
  return (
    <footer className="bg-slate-50 dark:bg-slate-900/50 py-12 px-6 border-t border-slate-200 dark:border-slate-800">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
        <div className="flex items-center gap-2 grayscale opacity-50">
          <div className="w-6 h-6 bg-slate-900 dark:bg-white rounded-md" />
          <span className="text-sm font-extrabold tracking-tighter">
            SENTINEL
          </span>
        </div>

        <div className="flex gap-8 text-sm font-semibold text-slate-500">
          <a className="hover:text-primary" href="#">
            Terms
          </a>
          <a className="hover:text-primary" href="#">
            API Docs
          </a>
          <a className="hover:text-primary" href="#">
            System Health
          </a>
          <a className="hover:text-primary" href="#">
            Security
          </a>
        </div>

        <p className="text-xs text-slate-400 font-medium">
          © 2024 Sentinel Predictive Maintenance Systems. Proprietary and
          Confidential.
        </p>
      </div>
    </footer>
  );
}
