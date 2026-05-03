export default function ReportHeader() {
  return (
    <header className="flex justify-between items-start border-b-2 border-primary pb-8 mb-8">
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2 mb-2">
          <span className="material-icons-round text-primary">shield</span>
          <span className="text-sm font-bold tracking-widest uppercase text-slate-400">
            Sentinel Maintenance Platform
          </span>
        </div>
        <h1 className="text-4xl font-black text-slate-900 tracking-tight leading-none uppercase">
          Maintenance Work Order
        </h1>
        <p className="text-slate-500 font-medium">
          Auto-generated via AI Diagnostic Core • 24 Oct 2023
        </p>
      </div>
      <div className="text-right">
        <div className="inline-block px-4 py-1.5 bg-red-100 text-red-700 rounded-full text-sm font-bold uppercase tracking-wider mb-4 border border-red-200">
          High Priority
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-xs font-bold text-slate-400 uppercase">Ticket ID</span>
          <span className="text-lg font-bold text-slate-900 leading-none">MT-8842-X04</span>
        </div>
      </div>

    </header>
  );
}