import { useEffect, useMemo, useState } from "react";
import { useKnowledgeStore } from "../../stores/useKnowledgeStore";

function inferType(title = "") {
  const t = title.toLowerCase();
  if (t.includes("iso") || t.includes("standard")) return "Standard";
  if (t.includes("manual") || t.includes("spec") || t.includes("bearing") || t.includes("guide")) return "Manual";
  return "Report";
}

function inferIcon(type) {
  if (type === "Standard") return "description";
  if (type === "Manual")   return "settings_applications";
  return "analytics";
}

function typeBadge(type) {
  if (type === "Standard") return "bg-primary/10 text-primary";
  if (type === "Manual")   return "bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400";
  return "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400";
}

export default function DocumentLibrary() {
  const { chunks, chunksLoading, fetchDocuments } = useKnowledgeStore();
  const [sortBy, setSortBy] = useState("Recently Added");

  useEffect(() => {
    fetchDocuments();
  }, []);

  const docs = useMemo(() => {
    const seen = new Set();
    const fromChunks = chunks
      .map((c) => {
        const filename = c.source || "";
        const title    = filename.replace(".pdf", "").replace(/_/g, " ");
        const type     = inferType(title);
        const chunkCount = chunks.filter((x) => x.source === filename).length;
        return { filename, title, type, icon: inferIcon(type), chunkCount };
      })
      .filter((d) => {
        if (!d.filename || seen.has(d.filename)) return false;
        seen.add(d.filename);
        return true;
      });

    if (sortBy === "Document Type") {
      return [...fromChunks].sort((a, b) => a.type.localeCompare(b.type));
    }
    if (sortBy === "Name A–Z") {
      return [...fromChunks].sort((a, b) => a.title.localeCompare(b.title));
    }
    return fromChunks;
  }, [chunks, sortBy]);

  return (
    <section>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-2xl font-display font-bold">Document Library</h3>
          {docs.length > 0 && (
            <p className="text-xs text-slate-400 mt-0.5">{docs.length} document{docs.length !== 1 ? "s" : ""} indexed</p>
          )}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Sort by:</span>
          <select
            className="bg-transparent border-none text-sm font-bold text-primary focus:ring-0 cursor-pointer"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option>Recently Added</option>
            <option>Document Type</option>
            <option>Name A–Z</option>
          </select>
        </div>
      </div>

      {chunksLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-cards-light dark:bg-cards-dark p-4 rounded-[2rem] border border-slate-200 dark:border-slate-700 animate-pulse">
              <div className="aspect-[3/4] bg-slate-100 dark:bg-slate-900 rounded-2xl mb-4" />
              <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded mb-2 w-3/4" />
              <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : docs.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <span className="material-symbols-rounded text-5xl text-slate-300 mb-4">folder_open</span>
          <p className="text-slate-500 font-semibold">No documents indexed yet</p>
          <p className="text-slate-400 text-sm mt-1">Upload a PDF manual above to get started</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {docs.map((d) => (
            <div
              key={d.filename}
              className="group bg-cards-light dark:bg-cards-dark p-4 rounded-[2rem] border border-slate-200 dark:border-slate-700 hover:shadow-xl transition-all hover:-translate-y-1"
            >
              <div className="aspect-[3/4] bg-slate-100 dark:bg-slate-900 rounded-2xl mb-4 flex flex-col items-center justify-center overflow-hidden relative gap-2 px-4">
                <span className="material-symbols-rounded text-5xl text-slate-300 dark:text-slate-700">
                  {d.icon}
                </span>
                <p className="text-[10px] text-slate-400 text-center font-mono line-clamp-3 px-2">
                  {d.filename}
                </p>
                <div className="absolute inset-0 bg-primary/0 group-hover:bg-primary/10 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                  <button className="bg-white text-primary p-2 rounded-full shadow-lg" aria-label="View">
                    <span className="material-symbols-rounded">visibility</span>
                  </button>
                </div>
              </div>

              <h4 className="font-bold text-sm truncate mb-1" title={d.title}>{d.title}</h4>
              <div className="flex items-center justify-between">
                <span className={`text-[10px] font-bold px-2 py-1 rounded-md uppercase ${typeBadge(d.type)}`}>
                  {d.type}
                </span>
                <span className="text-[10px] text-slate-400">{d.chunkCount} chunks</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
