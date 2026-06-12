import { useEffect, useRef, useState } from "react";
import { useConsultingStore } from "../../stores/useConsultingStore";

function logClass(type) {
  switch (type) {
    case "good":    return "text-green-500";
    case "warn":    return "text-yellow-500 bg-yellow-500/10 p-1 rounded";
    case "bad":     return "text-red-500 font-bold bg-red-500/10 p-1 rounded";
    case "bad2":    return "text-red-500";
    case "primary": return "text-primary";
    case "info":    return "text-slate-400";
    case "query":   return "text-blue-400";
    case "success": return "text-green-400";
    case "error":   return "text-red-400";
    default:        return "text-slate-500";
  }
}

function nowTime() {
  return new Date().toTimeString().slice(0, 8);
}

const BOOT_LOGS = [
  { t: "—", type: "muted",   text: "Connecting to Sentinel AI service..." },
  { t: "—", type: "info",    text: "Subscribed to consulting service at localhost:8002" },
  { t: "—", type: "success", text: "FEED_ACTIVE: Waiting for diagnostic queries..." },
];

export default function TelemetryPanel() {
  const { isLoading, rawAnswer, error, sources } = useConsultingStore();
  const [logs, setLogs] = useState(BOOT_LOGS);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (isLoading) {
      setLogs((prev) => [
        ...prev,
        { t: nowTime(), type: "query",   text: "CONSULTING_SERVICE: RAG query received" },
        { t: nowTime(), type: "query",   text: "RAG_ENGINE: Searching indexed documentation..." },
        { t: nowTime(), type: "primary", text: "SENTINEL_AI: Generating diagnosis from context chunks..." },
      ]);
    }
  }, [isLoading]);

  useEffect(() => {
    if (rawAnswer && !isLoading) {
      const srcList = sources.map((s) => s.file ?? s.source ?? "—").join(", ");
      setLogs((prev) => [
        ...prev,
        { t: nowTime(), type: "success", text: "RAG_ENGINE: Context retrieved successfully" },
        { t: nowTime(), type: "success", text: `SOURCES: ${srcList || "indexed documents"}` },
        { t: nowTime(), type: "primary", text: "SENTINEL_AI: Diagnosis complete — result delivered to panel" },
      ]);
    }
  }, [rawAnswer]);

  useEffect(() => {
    if (error && !isLoading) {
      setLogs((prev) => [
        ...prev,
        { t: nowTime(), type: "query", text: "CONSULTING_SERVICE: Request dispatched" },
        { t: nowTime(), type: "error", text: `SENTINEL_AI: Error — ${error}` },
      ]);
    }
  }, [error]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className="w-2/5 flex flex-col border-r border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-white dark:bg-card-dark">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Live Telemetry Logs
        </span>
        <div className="flex gap-2 items-center">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-[10px] font-mono text-slate-400">FEED_ACTIVE: 2.4kb/s</span>
        </div>
      </div>

      <div className="flex-1 p-4 font-mono text-xs overflow-y-auto terminal-scroll space-y-2">
        {logs.map((l, idx) => (
          <div key={idx} className={logClass(l.type)}>
            [{l.t}] {l.text}
          </div>
        ))}
        {isLoading && <div className="text-blue-400 animate-pulse">▋</div>}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
