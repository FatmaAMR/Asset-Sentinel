export default function AlertsSidebar() {
  return (
    <div className="space-y-8">
      <div className="bg-cards-light rounded-3xl p-6 border border-gray-100 shadow-sm flex flex-col">
        <h3 className="text-lg font-bold mb-6 flex items-center justify-between">
          Instant Alerts
          <span className="text-[10px] bg-failure text-white px-2 py-0.5 rounded-full">3 New</span>
        </h3>
        <div className="space-y-4 flex-grow">
          <div className="p-4 bg-failure/5 border-l-4 border-failure rounded-xl">
            <div className="flex justify-between items-start mb-2">
              <span className="text-xs font-bold text-failure">CRITICAL BREACH</span>
              <span className="text-[10px] text-slate-400">2m ago</span>
            </div>
            <p className="text-sm font-medium leading-snug text-slate-600">
              Motor 12: Velocity exceeds 11.2 mm/s limit (ISO 10816-3)
            </p>
            <div className="mt-3 flex gap-2">
              <button className="text-[10px] font-bold bg-failure text-white px-3 py-1.5 rounded-lg">
                AI Diagnosis
              </button>
              <button className="text-[10px] font-bold bg-white px-3 py-1.5 rounded-lg border border-gray-200">
                Ignore
              </button>
            </div>
          </div>
          <div className="p-4 bg-warning/5 border-l-4 border-warning rounded-xl">
            <div className="flex justify-between items-start mb-2">
              <span className="text-xs font-bold text-warning">WARNING</span>
              <span className="text-[10px] text-slate-400">14m ago</span>
            </div>
            <p className="text-sm font-medium leading-snug text-slate-600">
              Pump C7: Misalignment signature detected in spectrum.
            </p>
          </div>
          <div className="p-4 bg-gray-50 border-l-4 border-gray-300 rounded-xl">
            <div className="flex justify-between items-start mb-2">
              <span className="text-xs font-bold text-slate-500">SYSTEM</span>
              <span className="text-[10px] text-slate-400">1h ago</span>
            </div>
            <p className="text-sm font-medium leading-snug text-slate-500">
              Firmware update v2.4.1 deployed to Field Gateway 04.
            </p>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t border-gray-100 space-y-3">
          <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2">Quick Actions</p>
          <button className="w-full flex items-center justify-between p-3 rounded-2xl bg-primary text-white font-semibold text-sm hover:scale-[1.02] transition-transform">
            Generate Diagnostic Report
            <span className="material-icons-round text-lg">auto_awesome</span>
          </button>
          <button className="w-full flex items-center justify-between p-3 rounded-2xl bg-slate-100 text-slate-600 font-semibold text-sm hover:bg-slate-200 transition-colors">
            Dismiss All Non-Critical
            <span className="material-icons-round text-lg">done_all</span>
          </button>
        </div>
      </div>
      <div className="bg-primary/5 rounded-3xl p-6 border border-primary/10">
        <h4 className="text-sm font-bold mb-4">Maintenance Progress</h4>
        <div className="flex items-center gap-4 mb-4">
          <div className="w-16 h-16 rounded-full border-4 border-primary border-r-transparent flex items-center justify-center">
            <span className="text-xs font-bold">72%</span>
          </div>
          <div>
            <p className="text-xs text-slate-500">Fleet Uptime Target</p>
            <p className="text-sm font-bold">Ahead of schedule</p>
          </div>
        </div>
        <button className="w-full py-2 bg-white rounded-xl text-xs font-bold text-primary border border-primary/20">
          Schedule Inspections
        </button>
      </div>

    </div>
  );
}