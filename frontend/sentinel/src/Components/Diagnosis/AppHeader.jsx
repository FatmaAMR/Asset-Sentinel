export default function AppHeader() {
  return (
    <header className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-card-dark sticky top-0 z-50">
      <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-white">
              <span className="material-symbols-rounded text-xl">insights</span>
            </div>
            <span className="font-extrabold text-xl tracking-tight uppercase">
              Sentinel
            </span>
          </div>

          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-500 dark:text-slate-400">
            <a className="hover:text-primary transition-colors" href="#">
              Fleet Health
            </a>
            <a
              className="text-primary border-b-2 border-primary pb-5 pt-5"
              href="#"
            >
              Asset Diagnosis
            </a>
            <a className="hover:text-primary transition-colors" href="#">
              Technical Docs
            </a>
            <a className="hover:text-primary transition-colors" href="#">
              Maintenance Logs
            </a>
          </nav>
        </div>

        <div className="flex items-center gap-4">
          <button className="p-2 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full">
            <span className="material-symbols-rounded">notifications</span>
          </button>

          <div className="h-8 w-px bg-slate-200 dark:bg-slate-700" />

          <button className="bg-primary hover:opacity-90 text-white px-4 py-2 rounded-full text-sm font-semibold flex items-center gap-2 transition-all">
            <span className="material-symbols-rounded text-sm">assignment</span>
            Create Ticket
          </button>
        </div>
      </div>
    </header>
  );
}
