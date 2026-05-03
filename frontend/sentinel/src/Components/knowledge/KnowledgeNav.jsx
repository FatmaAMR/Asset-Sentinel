import { NavLink } from "react-router-dom";

export default function KnowledgeNav({ dark, onToggleDark }) {
  return (
    <nav className="sticky top-0 z-50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
            <span className="material-symbols-rounded text-white">
              shield_with_heart
            </span>
          </div>
          <span className="text-xl font-display font-extrabold tracking-tight">
            SENTINEL
          </span>
        </div>

        <div className="hidden md:flex items-center gap-8">
          <a
            className="text-sm font-semibold hover:text-primary transition-colors"
            href="#"
          >
            Fleet Health
          </a>
          <NavLink
            to="/diagnosis"
            className={({ isActive }) =>
              `text-sm font-semibold transition-colors ${
                isActive ? "text-primary" : "hover:text-primary"
              }`
            }
          >
            Diagnostics
          </NavLink>
          <NavLink
            to="/knowledge"
            className={({ isActive }) =>
              `text-sm font-semibold transition-colors ${
                isActive ? "text-primary" : "hover:text-primary"
              }`
            }
          >
            Knowledge Base
          </NavLink>
          <a
            className="text-sm font-semibold hover:text-primary transition-colors"
            href="#"
          >
            Settings
          </a>
        </div>

        <div className="flex items-center gap-4">
          <button
            className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800"
            onClick={onToggleDark}
            aria-label="Toggle dark mode"
            title={dark ? "Light mode" : "Dark mode"}
          >
            <span className="material-symbols-rounded">dark_mode</span>
          </button>

          <button className="bg-primary text-white px-6 py-2.5 rounded-full font-bold text-sm shadow-lg shadow-primary/20 hover:scale-105 transition-transform">
            Sign Out
          </button>
        </div>
      </div>
    </nav>
  );
}
