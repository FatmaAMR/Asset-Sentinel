import { useState } from "react";
export default function ExportSidebar() {
  const [includeAI, setIncludeAI] = useState(true);
  const [rawData, setRawData] = useState(false);

  return (
    <aside className="w-72 bg-cards-light border-r border-slate-200 p-6 flex flex-col gap-8 sticky top-0 h-screen">
      <div className="flex items-center gap-3">
        <div className="bg-primary p-1.5 rounded-lg text-white">
          <span className="material-icons-round text-2xl">analytics</span>
        </div>
        <h2 className="text-xl font-bold tracking-tight">Sentinel</h2>
      </div>

      <div className="flex flex-col gap-6">
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">
            Export Options
          </h3>
          <div className="space-y-2">
            <button
              onClick={() => window.print()}
              className="w-full flex items-center gap-3 px-3 py-2.5 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 transition-all shadow-sm"
            >
              <span className="material-icons-round text-xl">print</span>
              Print Report
            </button>
            <button className="w-full flex items-center gap-3 px-3 py-2.5 bg-light text-slate-700 rounded-lg font-medium hover:bg-slate-100 transition-all">
              <span className="material-icons-round text-xl">picture_as_pdf</span>
              Download PDF
            </button>
            <button className="w-full flex items-center gap-3 px-3 py-2.5 bg-light text-slate-700 rounded-lg font-medium hover:bg-slate-100 transition-all">
              <span className="material-icons-round text-xl">ios_share</span>
              Share Link
            </button>
          </div>
        </div>
        <div className="pt-6 border-t border-slate-100">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">
            Report Settings
          </h3>
          <div className="space-y-4">
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-sm text-slate-600 font-medium">Include AI Analysis</span>
              <div className="relative inline-flex items-center">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={includeAI}
                  onChange={() => setIncludeAI(!includeAI)}
                />
                <div className="w-9 h-5 bg-gray-200 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary" />
              </div>
            </label>
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-sm text-slate-600 font-medium">Raw Data Tables</span>
              <div className="relative inline-flex items-center">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={rawData}
                  onChange={() => setRawData(!rawData)}
                />
                <div className="w-9 h-5 bg-gray-200 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary" />
              </div>
            </label>

          </div>
        </div>
      </div>
      <div className="mt-auto">
        <div className="p-4 bg-primary/5 rounded-xl border border-primary/10">
          <p className="text-xs font-medium text-primary mb-1">Ticket Status</p>
          <p className="text-sm font-bold text-slate-900">Pending Technical Review</p>
          <div className="mt-3 w-full bg-slate-200 rounded-full h-1.5">
            <div className="bg-primary h-1.5 rounded-full w-3/4" />
          </div>
        </div>
      </div>

    </aside>
  );
}