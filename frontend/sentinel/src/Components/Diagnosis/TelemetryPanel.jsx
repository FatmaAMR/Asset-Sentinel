import { useEffect, useRef } from "react";
import { useConsultingStore } from "../../stores/useConsultingStore";

const initialLogs = [
  { t: "08:24:10", type: "muted",   text: "Connecting to MQTT broker..." },
  { t: "08:24:11", type: "muted",   text: "Subscribed to /assets/TRB-9402/sensors/#" },
  { t: "08:24:12", type: "good",    text: "DATA_RECEIVED: RPM=3600, TEMP=842C, VIB=12.4mm/s" },
  { t: "08:24:15", type: "info",    text: "LOG_INFO: Lubrication pressure stable at 4.2 bar" },
  { t: "08:24:18", type: "warn",    text: "ALERT: Bearing temperature oscillation detected (+/- 4C)" },
  { t: "08:24:22", type: "bad",     text: "CRITICAL: Vibration threshold exceeded ISO 10816 Zone C" },
  { t: "08:24:25", type: "info",    text: "LOG_INFO: Triggering Sentinel AI Diagnostic Routine..." },
  { t: "08:24:26", type: "primary", text: "SENTINEL_AI: Local LLM (Llama-3-70B) processing context..." },
  { t: "08:24:28", type: "info",    text: "RAG_ENGINE: Searching ISO-10816 and SKF-Bearing-Manual-2023..." },
  { t: "08:24:30", type: "info",    text: "LOG_INFO: Telemetry snapshot stored in session_cache_094" },
  { t: "08:24:32", type: "muted",   text: "DATA_RECEIVED: RPM=3600, TEMP=843C, VIB=12.6mm/s" },
  { t: "08:24:35", type: "muted",   text: "DATA_RECEIVED: RPM=3601, TEMP=844C, VIB=12.9mm/s" },
  { t: "08:24:38", type: "muted",   text: "DATA_RECEIVED: RPM=3599, TEMP=844C, VIB=13.1mm/s" },
  { t: "08:24:40", type: "bad2",    text: "ALERT: Peak vibration amplitude 13.4mm/s" },
];

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

export default function TelemetryPanel() {
  const { isLoading, rawAnswer, error, sources } = useConsultingStore();
  const bottomRef = useRef(null);

  const dynamicLogs = [...initialLogs];

  if (isLoading) {
    dynamicLogs.push(
      { t: nowTime(), type: "query",   text: "CONSULTING_SERVICE: RAG query received" },
      { t: nowTime(), type: "query",   text: "RAG_ENGINE: Searching indexed documentation..." },
      { t: nowTime(), type: "primary", text: "SENTINEL_AI: Generating diagnosis from context chunks..." },
    );
  }

  if (rawAnswer && !isLoading) {
    const srcList = sources.map((s) => s.file ?? s.source ?? "—").join(", ");
    dynamicLogs.push(
      { t: nowTime(), type: "success", text: "RAG_ENGINE: Context retrieved successfully" },
      { t: nowTime(), type: "success", text: `SOURCES: ${srcList || "indexed documents"}` },
      { t: nowTime(), type: "primary", text: "SENTINEL_AI: Diagnosis complete — result delivered to panel" },
    );
  }

  if (error && !isLoading) {
    dynamicLogs.push(
      { t: nowTime(), type: "query", text: "CONSULTING_SERVICE: Request dispatched" },
      { t: nowTime(), type: "error", text: `SENTINEL_AI: Error — ${error}` },
    );
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [isLoading, rawAnswer, error]);

  return (
    <div className="w-2/5 flex flex-col border-r border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-white dark:bg-card-dark">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Live Telemetry Logs
        </span>
        <div className="flex gap-2 items-center">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-[10px] font-mono text-slate-400">
            FEED_ACTIVE: 2.4kb/s
          </span>
        </div>
      </div>

      {/* Log entries */}
      <div className="flex-1 p-4 font-mono text-xs overflow-y-auto terminal-scroll space-y-2">
        {dynamicLogs.map((l, idx) => (
          <div key={idx} className={logClass(l.type)}>
            [{l.t}] {l.text}
          </div>
        ))}

        {isLoading && (
          <div className="text-blue-400 animate-pulse">▋</div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
