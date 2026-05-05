import { Link, useLocation } from "react-router-dom";
import useManagerialStore from "../stores/managerialStore";

export default function Navbar() {
  const location = useLocation();
  const token = useManagerialStore((state) => state.token);
  const logout = useManagerialStore((state) => state.logout);

  const isActive = (path) => location.pathname === path;

  const linkClass = (path) =>
    isActive(path)
      ? "text-primary border-b-2 border-primary pb-5 mt-5"
      : "hover:text-primary transition-colors";

  return (
    <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200">
      <div className="max-w-[1440px] mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="material-icons-round text-white text-xl">security</span>
            </div>
            <span className="text-xl font-bold tracking-tight">SENTINEL</span>
          </div>
          <div className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-500">
            <Link to="/" className={linkClass("/")}>Dashboard</Link>
            <Link to="/knowledge" className={linkClass("/knowledge")}>Knowledge Base</Link>
            <Link to="/diagnosis" className={linkClass("/diagnosis")}>Diagnostics</Link>
            <Link to="/export" className={linkClass("/export")}>Reports</Link>
            <Link to="/config" className={linkClass("/config")}>System Config</Link>
            <Link to="/history" className={linkClass("/history")}>History & Trends</Link>
            <Link to="/assets" className={linkClass("/assets")}>Assets</Link>
            <Link to="/thresholds" className={linkClass("/thresholds")}>Thresholds</Link>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button className="p-2 hover:bg-gray-100 rounded-full transition-colors relative">
            <span className="material-icons-round">notifications</span>
            <span className="absolute top-2 right-2 w-2 h-2 bg-failure rounded-full border-2 border-white" />
          </button>
          <div className="h-8 w-px bg-gray-200 mx-2" />
          {token ? (
            <button
              onClick={logout}
              className="text-xs font-semibold text-failure hover:opacity-70 transition-opacity"
            >
              Logout
            </button>
          ) : (
            <Link to="/login" className="text-xs font-semibold text-primary hover:opacity-70 transition-opacity">
              Login
            </Link>
          )}
          <div className="text-right hidden sm:block">
            <p className="text-xs font-semibold">Eng. Sarah Chen</p>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest">Lead Operator</p>
          </div>
        </div>

      </div>

    </nav>
  );
}