/* eslint-disable react/prop-types */
import { useState } from "react";
import { useQueryingStore } from "../stores/Usequeryingstore";

const SUGGESTED_QUERIES = [
  { icon: "trending_down", label: "Lowest RUL machines", question: "Show me the 5 machines with the lowest remaining useful life, return machine_id, label and rul" },
  { icon: "warning", label: "Machines needing alerts", question: "Show machines where label is WARNING or CRITICAL, return machine_id, label and rul ordered by rul ascending" },
  { icon: "category", label: "All health labels", question: "Show me all distinct machine labels and how many machines have each label" },
  { icon: "schedule", label: "Latest readings", question: "Show me 10 machines with their machine_id, label and rul ordered by rul ascending" },
{ icon: "analytics", label: "Average RUL by label", question: "SELECT label, COUNT(*) as machine_count, ROUND(AVG(CAST(rul AS REAL)), 2) as avg_rul FROM assets GROUP BY label ORDER BY avg_rul ASC" },
  { icon: "crisis_alert", label: "Critical machines", question: "Show all machines where label is CRITICAL or WARNING, return machine_id, label and rul ordered by rul ascending" },
];

// eslint-disable-next-line react/prop-types
function ResultTable({ results }) {
  // eslint-disable-next-line react/prop-types
  if (!results || results.length === 0) return null;
  const columns = Object.keys(results[0]);

  return (
    <div className="overflow-x-auto rounded-2xl border border-gray-100 shadow-sm">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-100 bg-slate-50/80">
            {columns.map((col) => (
              <th key={col} className="text-left text-xs font-bold text-slate-400 uppercase tracking-wider px-6 py-4">
                {col.replace(/_/g, " ")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {results.map((row, i) => (
            <tr key={i} className={`border-b border-gray-50 hover:bg-primary/5 transition-colors ${i % 2 === 0 ? "bg-white" : "bg-slate-50/50"}`}>
              {columns.map((col) => (
                <td key={col} className="px-6 py-4 text-sm font-mono text-slate-700">
                  {col === "label" ? (
                    <span className={`text-[10px] font-bold px-2 py-1 rounded-full uppercase ${
                      row[col] === "HEALTHY" ? "bg-green-100 text-green-600" :
                      row[col] === "CRITICAL" ? "bg-red-100 text-red-600" :
                      row[col] === "WARNING" ? "bg-yellow-100 text-yellow-600" :
                      "bg-slate-100 text-slate-500"
                    }`}>
                      {row[col] ?? "—"}
                    </span>
                  ) : (
                    row[col] ?? "—"
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SqlBadge({ sql }) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-2xl bg-slate-900 p-4 relative group">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Generated SQL</span>
        <button onClick={copy} className="text-[10px] text-slate-500 hover:text-slate-300 transition-colors flex items-center gap-1">
          <span className="material-symbols-rounded text-xs">{copied ? "check" : "content_copy"}</span>
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <code className="text-xs text-blue-300 font-mono whitespace-pre-wrap">{sql}</code>
    </div>
  );
}

export default function DataExplorer() {
  const {
    question, isLoading, error, result, history,
    setQuestion, ask, clearResult,
  } = useQueryingStore();

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !isLoading) ask();
  };

  return (
    <div className="p-8 max-w-[1440px] mx-auto">

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
            <span className="w-9 h-9 bg-primary rounded-xl flex items-center justify-center text-white shadow-lg shadow-primary/30">
              <span className="material-symbols-rounded text-lg">manage_search</span>
            </span>
            Data Explorer
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Ask questions about your fleet in plain English — powered by the Querying Inference Service
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 border border-green-100 rounded-full">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-xs font-semibold text-green-600">Query Service Online</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-8">

        {/* Left: Input + Results */}
        <div className="col-span-12 lg:col-span-8 space-y-6">

          {/* Search bar */}
          <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-6">
            <label className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 block">
              Natural Language Query
            </label>
            <div className="relative">
              <input
                className="w-full bg-slate-50 border border-gray-200 rounded-2xl py-4 px-6 pr-16 text-sm focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 transition-all"
                placeholder="e.g. Show me machines with RUL below 70..."
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isLoading}
              />
              <button
                onClick={() => ask()}
                disabled={isLoading || !question.trim()}
                className="absolute right-3 top-2 bottom-2 aspect-square bg-primary text-white rounded-xl flex items-center justify-center hover:scale-105 transition-transform disabled:opacity-40 disabled:cursor-not-allowed disabled:scale-100 shadow-lg shadow-primary/30"
              >
                {isLoading ? (
                  <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                ) : (
                  <span className="material-symbols-rounded text-lg">send</span>
                )}
              </button>
            </div>
          </div>

          {/* Results */}
          {(isLoading || result || error) && (
            <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-6 space-y-5">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-slate-800 flex items-center gap-2">
                  <span className="material-symbols-rounded text-primary text-lg">table_view</span>
                  Query Results
                </h3>
                {result && (
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-400 font-mono">
                      {result.results.length} row{result.results.length !== 1 ? "s" : ""} returned
                    </span>
                    <button onClick={clearResult} className="text-slate-400 hover:text-slate-600 transition-colors">
                      <span className="material-symbols-rounded text-sm">close</span>
                    </button>
                  </div>
                )}
              </div>

              {isLoading && (
                <div className="flex items-center gap-3 text-slate-500 text-sm py-8 justify-center">
                  <span className="w-5 h-5 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                  <span>Generating SQL and querying database...</span>
                </div>
              )}

              {error && !isLoading && (
                <div className="p-4 rounded-2xl bg-red-50 border border-red-100 text-red-600 text-sm flex items-start gap-3">
                  <span className="material-symbols-rounded text-lg flex-shrink-0">error</span>
                  <div>
                    <p className="font-bold mb-1">Query failed</p>
                    <p>{error}</p>
                  </div>
                </div>
              )}

              {result && !isLoading && (
                <div className="space-y-4">
                  <p className="text-sm text-slate-500 italic">&quot;{result.question}&quot; </p>
                  <SqlBadge sql={result.sql} />
                  {result.results.length > 0 ? (
                    <ResultTable results={result.results} />
                  ) : (
                    <div className="text-center py-8 text-slate-400">
                      <span className="material-symbols-rounded text-3xl block mb-2">search_off</span>
                      <p className="text-sm">No rows matched this query.</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Query History */}
          {history.length > 0 && (
            <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-6">
              <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                <span className="material-symbols-rounded text-slate-400 text-lg">history</span>
                Recent Queries
              </h3>
              <div className="space-y-2">
                {history.slice(0, 5).map((h, i) => (
                  <button
                    key={i}
                    onClick={() => ask(h.question)}
                    className="w-full text-left px-4 py-3 rounded-xl bg-slate-50 hover:bg-primary/5 hover:border-primary/20 border border-transparent transition-all group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-600 group-hover:text-primary transition-colors truncate pr-4">
                        {h.question}
                      </span>
                      <span className="text-xs text-slate-400 flex-shrink-0">
                        {h.results.length} rows
                      </span>
                    </div>
                    <code className="text-[10px] text-slate-400 font-mono mt-1 block truncate">
                      {h.sql}
                    </code>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: Suggested queries + Schema */}
        <div className="col-span-12 lg:col-span-4 space-y-6">

          {/* Suggested queries */}
          <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-6">
            <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
              <span className="material-symbols-rounded text-primary text-lg">lightbulb</span>
              Suggested Queries
            </h3>
            <div className="space-y-2">
              {SUGGESTED_QUERIES.map((q) => (
                <button
                  key={q.label}
                  onClick={() => ask(q.question)}
                  disabled={isLoading}
                  className="w-full text-left px-4 py-3 rounded-xl bg-slate-50 hover:bg-primary/5 border border-transparent hover:border-primary/20 transition-all group disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-3"
                >
                  <span className="material-symbols-rounded text-slate-400 group-hover:text-primary transition-colors text-lg flex-shrink-0">
                    {q.icon}
                  </span>
                  <span className="text-sm text-slate-600 group-hover:text-primary transition-colors">
                    {q.label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Schema reference */}
          <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-6">
            <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
              <span className="material-symbols-rounded text-slate-400 text-lg">schema</span>
              Schema Reference
            </h3>
            <div className="bg-slate-900 rounded-2xl p-4">
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-3">Table: assets</p>
              {[
                { col: "machine_id", type: "TEXT", note: "e.g. 'machine-68'" },
                { col: "label", type: "TEXT", note: "HEALTHY / WARNING / CRITICAL" },
                { col: "rul", type: "TEXT", note: "cast to REAL for math" },
                { col: "timestamp", type: "TEXT", note: "ISO datetime" },
                { col: "message_id", type: "TEXT", note: "unique UUID" },
                { col: "should_alert", type: "TEXT", note: "'True' or 'False'" },
                { col: "alert_level", type: "TEXT", note: "raw pipeline level" },
              ].map((f) => (
                <div key={f.col} className="flex items-start gap-2 mb-2">
                  <code className="text-xs text-blue-300 font-mono flex-shrink-0">{f.col}</code>
                  <span className="text-[10px] text-slate-500 font-mono">{f.type}</span>
                  <span className="text-[10px] text-slate-600 ml-auto text-right">{f.note}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Stats */}
          <div className="bg-primary rounded-3xl p-6 text-white shadow-lg shadow-primary/20">
            <p className="text-xs font-bold uppercase tracking-widest opacity-70 mb-1">Query Service</p>
            <p className="text-2xl font-bold mb-1">localhost:8000</p>
            <p className="text-sm opacity-70">GET /ask?question=...</p>
            <div className="mt-4 pt-4 border-t border-white/20 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-300 animate-pulse" />
              <span className="text-sm font-semibold">Connected · qwen2.5:1.5b</span>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}