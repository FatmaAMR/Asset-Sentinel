import { useMemo, useState } from "react";

const docsSeed = [
  {
    title: "ISO-9001-Quality-Mgmt",
    type: "Standard",
    size: "12.4 MB",
    icon: "description",
  },
  {
    title: "Bearing-Spec-NTN-2024",
    type: "Manual",
    size: "4.1 MB",
    icon: "settings_applications",
  },
  {
    title: "Turbine-Health-Telemetry",
    type: "Report",
    size: "8.9 MB",
    icon: "analytics",
  },
];

function typeBadge(type) {
  if (type === "Standard") return "bg-primary/10 text-primary";
  if (type === "Manual")
    return "bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400";
  return "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400";
}

export default function DocumentLibrary() {
  const [sortBy, setSortBy] = useState("Recently Added");

  const docs = useMemo(() => {
    if (sortBy === "Document Type") {
      return [...docsSeed].sort((a, b) => a.type.localeCompare(b.type));
    }
    return docsSeed; // placeholder
  }, [sortBy]);

  return (
    <section>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-2xl font-display font-bold">Document Library</h3>

        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">
            Sort by:
          </span>
          <select
            className="bg-transparent border-none text-sm font-bold text-primary focus:ring-0 cursor-pointer"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option>Recently Added</option>
            <option>Document Type</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
        {docs.map((d) => (
          <div
            key={d.title}
            className="group bg-cards-light dark:bg-cards-dark
           p-4 rounded-[2rem]
           border border-slate-200 dark:border-slate-700
           hover:shadow-xl transition-all hover:-translate-y-1"
          >
            <div className="aspect-[3/4] bg-slate-100 dark:bg-slate-900 rounded-2xl mb-4 flex items-center justify-center overflow-hidden relative">
              <span className="material-symbols-rounded text-5xl text-slate-300 dark:text-slate-700">
                {d.icon}
              </span>

              <div className="absolute inset-0 bg-primary/0 group-hover:bg-primary/10 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                <button
                  className="bg-white text-primary p-2 rounded-full shadow-lg"
                  aria-label="View"
                >
                  <span className="material-symbols-rounded">visibility</span>
                </button>
              </div>
            </div>

            <h4 className="font-bold text-sm truncate mb-1">{d.title}</h4>
            <div className="flex items-center justify-between">
              <span
                className={`text-[10px] font-bold px-2 py-1 rounded-md uppercase ${typeBadge(d.type)}`}
              >
                {d.type}
              </span>
              <span className="text-[10px] text-slate-400">{d.size}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
