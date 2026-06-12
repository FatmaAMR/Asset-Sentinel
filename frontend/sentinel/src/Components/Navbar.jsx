import { Link, useLocation } from "react-router-dom";
import { useState, useRef, useEffect } from "react";
import useManagerialStore from "../stores/managerialStore";
import { useConsultingStore } from "../stores/useConsultingStore";

export default function Navbar() {
  const location = useLocation();
  const token = useManagerialStore((state) => state.token);
  const logout = useManagerialStore((state) => state.logout);
  const user = useManagerialStore((state) => state.user);
  const notifications = useConsultingStore((s) => s.notifications);
  const unreadCount = useConsultingStore((s) => s.unreadCount);
  const markAllRead = useConsultingStore((s) => s.markAllRead);

  const [open, setOpen] = useState(false);
  const dropRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handler = (e) => {
      if (dropRef.current && !dropRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleBellClick = () => {
    setOpen((v) => !v);
    if (!open) markAllRead();
  };

  const isActive = (path) => location.pathname === path;
  const linkClass = (path) =>
    isActive(path)
      ? "text-primary border-b-2 border-primary pb-5 mt-5 font-bold"
      : "text-muted hover:text-primary transition-colors pb-5 mt-5 font-medium";

  const severityColor = (notif) => {
    const cause = (notif.fault_cause || "").toLowerCase();
    if (cause.includes("critical") || cause.includes("failure")) return "bg-red-500";
    if (cause.includes("warn") || cause.includes("degradat")) return "bg-yellow-500";
    return "bg-blue-500";
  };

  const formatTime = (ts) => {
    if (!ts) return "";
    return new Date(ts * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <nav className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-slate-200/60 shadow-sm">
      <div className="max-w-[1440px] mx-auto px-6 h-16 flex items-center justify-between">

        {/* Logo + Links */}
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <img src="/AssetSeninel.svg" alt="Asset Sentinel" className="w-8 h-8" />
            <span className="text-xl font-black tracking-tight text-primary">SENTINEL</span>
          </div>
          <div className="hidden md:flex items-center gap-6 text-sm h-16">
            <Link to="/" className={linkClass("/")}>Dashboard</Link>
            <Link to="/data-explorer" className={linkClass("/data-explorer")}>Data Explorer</Link>
            <Link to="/knowledge" className={linkClass("/knowledge")}>Knowledge Base</Link>
            <Link to="/diagnosis" className={linkClass("/diagnosis")}>Diagnostics</Link>
            {/* <Link to="/export"        className={linkClass("/export")}>Reports</Link>
            <Link to="/config"        className={linkClass("/config")}>System Config</Link>
            <Link to="/history"       className={linkClass("/history")}>History & Trends</Link> */}
            <Link to="/datasets" className={linkClass("/datasets")}>Datasets</Link>
            {/* <Link to="/thresholds"    className={linkClass("/thresholds")}>Thresholds</Link> */}
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-4">

          {/* Bell with dropdown */}
          <div className="relative" ref={dropRef}>
            <button
              onClick={handleBellClick}
              className="p-2 hover:bg-slate-100 rounded-full transition-colors relative flex items-center justify-center"
            >
              <span className="material-icons-round text-slate-700">notifications</span>
              {unreadCount > 0 ? (
                <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center border-2 border-white">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              ) : (
                <span className="absolute top-2 right-2 w-2 h-2 bg-failure rounded-full border border-white" />
              )}
            </button>

            {/* Dropdown */}
            {open && (
              <div className="absolute right-0 mt-2 w-96 bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden z-50">
                {/* Header */}
                <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
                  <div>
                    <p className="font-bold text-sm">Diagnosis Notifications</p>
                    <p className="text-[11px] text-slate-400">
                      {notifications.length > 0
                        ? `${notifications.length} event${notifications.length !== 1 ? "s" : ""} received`
                        : "No notifications yet"}
                    </p>
                  </div>
                  <span className="material-icons-round text-slate-400 text-lg">auto_awesome</span>
                </div>

                {/* List */}
                <div className="max-h-80 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <div className="px-4 py-8 text-center text-slate-400 text-sm">
                      <span className="material-icons-round text-3xl mb-2 block">notifications_none</span>
                      Waiting for diagnosis events…
                    </div>
                  ) : (
                    notifications.map((n, i) => (
                      <div
                        key={n.message_id || i}
                        className="px-4 py-3 border-b border-slate-50 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                      >
                        <div className="flex items-start gap-3">
                          <span className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${severityColor(n)}`} />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-2 mb-0.5">
                              <p className="text-xs font-bold text-slate-700 dark:text-slate-200 truncate">
                                {n.machine_id}
                              </p>
                              <span className="text-[10px] text-slate-400 whitespace-nowrap">
                                {formatTime(n.notified_at || n.timestamp)}
                              </span>
                            </div>
                            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed line-clamp-2">
                              {n.extracted_reason || n.fault_cause || "Diagnosis complete"}
                            </p>
                            {n.fault_cause && n.fault_cause !== n.extracted_reason && (
                              <p className="text-[10px] text-slate-400 mt-1 line-clamp-1 italic">
                                {n.fault_cause.slice(0, 100)}…
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>

                {/* Footer */}
                {notifications.length > 0 && (
                  <div className="px-4 py-2 border-t border-slate-100 dark:border-slate-800">
                    <Link
                      to="/diagnosis"
                      onClick={() => setOpen(false)}
                      className="text-xs text-primary font-semibold hover:underline"
                    >
                      View in Diagnostics →
                    </Link>
                  </div>
                )}
              </div>
            )}
          </div>

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
          {user && (
            <div className="text-right hidden sm:block">
              <p className="text-xs font-bold text-light">{user.email}</p>
              <p className="text-[10px] text-muted uppercase tracking-widest font-semibold">{user.role}</p>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}