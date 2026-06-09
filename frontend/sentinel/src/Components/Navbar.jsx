import { Link, useLocation } from "react-router-dom";
import useManagerialStore from "../stores/managerialStore";

export default function Navbar() {
  const location = useLocation();
  const token = useManagerialStore((state) => state.token);
  const logout = useManagerialStore((state) => state.logout);

  const isActive = (path) => location.pathname === path;

  const linkClass = (path) =>
    isActive(path)
      ? "text-primary border-b-2 border-primary pb-5 mt-5 font-bold"
      : "text-muted hover:text-primary transition-colors pb-5 mt-5 font-medium";

  return (
    <nav className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-slate-200/60 shadow-sm">
      <div className="max-w-[1440px] mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <img src="/AssetSeninel.svg" alt="Asset Sentinel" className="w-8 h-8" />
            <span className="text-xl font-black tracking-tight text-primary">SENTINEL</span>
          </div>
          <div className="hidden md:flex items-center gap-6 text-sm h-16">
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
          <button className="p-2 hover:bg-slate-100 rounded-full transition-colors relative flex items-center justify-center">
            <span className="material-icons-round text-slate-700">notifications</span>
            <span className="absolute top-2 right-2 w-2 h-2 bg-failure rounded-full border border-white" />
          </button>
          <div className="h-6 w-px bg-slate-200 mx-2" />
          {token ? (
            <button
              onClick={logout}
              className="text-xs font-semibold text-failure hover:opacity-80 transition-opacity"
            >
              Logout
            </button>
          ) : (
            <Link to="/login" className="text-xs font-semibold text-primary hover:opacity-80 transition-opacity">
              Login
            </Link>
          )}
          <div className="text-right hidden sm:block">
            <p className="text-xs font-bold text-light">Eng. Sarah Chen</p>
            <p className="text-[10px] text-muted uppercase tracking-widest font-semibold">Lead Operator</p>
          </div>
        </div>
      </div>
    </nav>
  );
}