import { useConsultingStore } from "../../stores/useConsultingStore";

export default function AssetTopBar() {
  const { machineId, rawAnswer, isLoading } = useConsultingStore();

  const alertLevel = rawAnswer
    ? (rawAnswer.toLowerCase().includes("critical") ? "CRITICAL"
      : rawAnswer.toLowerCase().includes("warning") ? "WARNING"
      : "NORMAL")
    : isLoading ? "SCANNING" : "NORMAL";

  const badgeStyle = {
    CRITICAL: "bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400",
    WARNING:  "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400",
    NORMAL:   "bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400",
    SCANNING: "bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400",
  }[alertLevel];

  const sessionTime = new Date().toLocaleString("en-US", {
    month: "numeric", day: "numeric", year: "numeric",
    hour: "numeric", minute: "2-digit", hour12: true,
  });

  return (
    <div className="px-8 py-4 bg-white dark:bg-card-dark border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
      <div>
        <h1 className="text-xl font-bold flex items-center gap-3">
          Asset #{machineId?.toUpperCase() || "—"}
          <span className={`px-2 py-0.5 rounded text-xs font-bold ${badgeStyle}`}>
            {alertLevel}
          </span>
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Diagnosis session started {sessionTime} • Machine ID: {machineId}
        </p>
      </div>
      
    </div>
  );
}
