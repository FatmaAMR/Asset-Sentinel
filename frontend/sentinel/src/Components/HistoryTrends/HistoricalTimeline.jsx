const rows = [
  {
    date: "Oct 24, 2023",
    asset: "RT-902",
    diag: "Bearing Misalignment",
    sev: "Critical",
    action: "Scheduled Refurbishment",
  },
  {
    date: "Oct 21, 2023",
    asset: "MOT-044",
    diag: "Voltage Fluctuations",
    sev: "Warning",
    action: "Sensor Re-calibration",
  },
  {
    date: "Oct 19, 2023",
    asset: "CONV-21",
    diag: "Normal Operation",
    sev: "Healthy",
    action: "Routine Lubrication",
  },
  {
    date: "Oct 15, 2023",
    asset: "RT-901",
    diag: "Imbalance Detected",
    sev: "Warning",
    action: "Weighted Balancing",
  },
];

function badge(sev) {
  if (sev === "Critical") {
    return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400";
  }
  if (sev === "Warning") {
    return "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400";
  }
  return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400";
}

function dot(sev) {
  if (sev === "Critical") return "bg-red-500";
  if (sev === "Warning") return "bg-amber-500";
  return "bg-emerald-500";
}

export default function HistoricalTimeline() {
  return (
    <section className="bg-white dark:bg-[#1E293B] rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
      <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">Historical Timeline</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Detailed logs of all maintenance actions and diagnoses
          </p>
        </div>

        <div className="relative w-64">
          <span className="material-icons-round absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">
            search
          </span>
          <input
            className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-sm focus:ring-primary focus:border-primary"
            placeholder="Search logs..."
            type="text"
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="bg-slate-50 dark:bg-slate-900/50 text-slate-500 dark:text-slate-300 font-semibold border-b border-slate-100 dark:border-slate-800">
              <th className="px-6 py-4">Date</th>
              <th className="px-6 py-4">Asset ID</th>
              <th className="px-6 py-4">Diagnosis</th>
              <th className="px-6 py-4">Severity</th>
              <th className="px-6 py-4">Action Taken</th>
              <th className="px-6 py-4 text-right">Details</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {rows.map((r) => (
              <tr
                key={r.date + r.asset}
                className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
              >
                <td className="px-6 py-4 font-medium">{r.date}</td>
                <td className="px-6 py-4 text-slate-500 dark:text-slate-400">
                  {r.asset}
                </td>
                <td className="px-6 py-4">{r.diag}</td>
                <td className="px-6 py-4">
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold ${badge(r.sev)}`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${dot(r.sev)}`}
                    />
                    {r.sev}
                  </span>
                </td>
                <td className="px-6 py-4">{r.action}</td>
                <td className="px-6 py-4 text-right">
                  <button className="p-1 hover:text-primary transition-colors">
                    <span className="material-icons-round text-lg">
                      open_in_new
                    </span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Showing 1 to 10 of 254 entries
        </p>

        <div className="flex items-center gap-2">
          <button
            className="p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30"
            disabled
          >
            <span className="material-icons-round text-sm">chevron_left</span>
          </button>
          <button className="w-8 h-8 rounded bg-primary text-white text-xs font-bold">
            1
          </button>
          <button className="w-8 h-8 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-bold">
            2
          </button>
          <button className="w-8 h-8 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-bold">
            3
          </button>
          <button className="p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800">
            <span className="material-icons-round text-sm">chevron_right</span>
          </button>
        </div>
      </div>
    </section>
  );
}
