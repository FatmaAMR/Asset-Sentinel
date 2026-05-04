import { Link } from "react-router-dom";


export default function Navbar() {
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
            <Link to="/" className="text-primary border-b-2 border-primary pb-5 mt-5">Dashboard</Link>
            <Link to="/knowledge" className="hover:text-primary transition-colors">Knowledge Base</Link>
            <Link to="/diagnosis" className="hover:text-primary transition-colors">Diagnostics</Link>
            <Link to="/export" className="hover:text-primary transition-colors">Reports</Link>
            <Link to="/config" className="hover:text-primary transition-colors">System Config</Link>
            <Link to="/history" className="hover:text-primary transition-colors">History & Trends</Link>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button className="p-2 hover:bg-gray-100 rounded-full transition-colors relative">
            <span className="material-icons-round">notifications</span>
            <span className="absolute top-2 right-2 w-2 h-2 bg-failure rounded-full border-2 border-white" />
          </button>
          <div className="h-8 w-px bg-gray-200 mx-2" />
          <div className="text-right hidden sm:block">
            <p className="text-xs font-semibold">Eng. Sarah Chen</p>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest">Lead Operator</p>
          </div>
        </div>

      </div>
    </nav>
  );
}