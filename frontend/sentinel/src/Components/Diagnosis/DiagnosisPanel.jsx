import { useEffect, useState, useRef } from "react";
import { useConsultingStore } from "../../stores/useConsultingStore";

const POLL_INTERVAL_MS = 10_000; // poll every 10 seconds

const QUICK_ACTIONS = [
  {
    label: "Compare with 2022 overhaul logs",
    isMachineQuery: true,
    query: "Compare current bearing wear patterns with 2022 overhaul logs",
  },
  {
    label: "Show vibration spectrogram",
    question:
      "What vibration frequency patterns indicate bearing failure according to ISO 20816?",
  },
  {
    label: "Estimate MTBF",
    question:
      "How is mean time between failures calculated for rolling element bearings?",
  },
];

export default function DiagnosisPanel() {
  const {
    isLoading,
    error,
    rootCause,
    recommendations,
    citation,
    sources,
    rawAnswer,
    notifications,
    notificationsLoading,
    notificationsError,
    machineId,
    setMachineId,
    fetchNotifications,
    clearNotifications,
    askConsulting,
    machineQuery,
  } = useConsultingStore();

  const [q, setQ]                   = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [machineInput, setMachineInput] = useState(machineId);
  const pollRef = useRef(null);

  // ── Polling ────────────────────────────────────────────────────────────
  const startPolling = (id) => {
    if (pollRef.current) clearInterval(pollRef.current);
    fetchNotifications(id);                         // immediate first fetch
    pollRef.current = setInterval(
      () => fetchNotifications(id),
      POLL_INTERVAL_MS
    );
  };

  useEffect(() => {
    startPolling(machineId);
    return () => clearInterval(pollRef.current);
  }, [machineId]);

  // ── Machine ID change ──────────────────────────────────────────────────
  const handleMachineChange = () => {
    const trimmed = machineInput.trim();
    if (!trimmed || trimmed === machineId) return;
    // Wipe all state before switching machines
    useConsultingStore.setState({
      notifications:      [],
      unreadCount:        0,
      rawAnswer:          null,
      rootCause:          null,
      recommendations:    [],
      citation:           null,
      sources:            [],
      error:              null,
      notificationsError: null,
    });
    setChatHistory([]);
    setMachineId(trimmed);
    
  };

  // ── Chat / quick actions ───────────────────────────────────────────────
  const handleSend = async (action) => {
    const text = action ? null : q;
    if (!action && (!text?.trim() || isLoading)) return;
    if (!action) setQ("");

    if (action?.isMachineQuery) {
      setChatHistory((prev) => [...prev, { role: "user", text: action.label }]);
      await machineQuery(action.query, machineId);
    } else {
      const questionText = action?.question ?? text;
      setChatHistory((prev) => [
        ...prev,
        { role: "user", text: questionText },
      ]);
      await askConsulting(questionText, 4);
    }

    const answer = useConsultingStore.getState().rawAnswer || "";
    setChatHistory((prev) => [
      ...prev,
      { role: "assistant", text: answer },
    ]);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !isLoading) handleSend(null);
  };

  // ── Latest notification metadata ───────────────────────────────────────
  const latestNotif = notifications[0] || null;
  const notifTimestamp = latestNotif?.notified_at
    ? new Date(latestNotif.notified_at * 1000).toLocaleString()
    : null;

  // ── Display values ─────────────────────────────────────────────────────
  const isActuallyLoading = isLoading || notificationsLoading;

  const latestExtractedReason = latestNotif?.extracted_reason || "";
  const latestFaultCause      = latestNotif?.fault_cause || "";

  const displayRootCause =
    latestExtractedReason || rootCause || "Awaiting Sentinel AI diagnosis...";

  const displayFaultCause =
    latestFaultCause || recommendations[0] || "Awaiting diagnosis...";

  const displayRecommendations =
    recommendations.length > 0
      ? recommendations
      : latestFaultCause
      ? [latestFaultCause]
      : [
          "Immediate reduction of turbine load to 60% capacity.",
          "Inspect lubricant for metallic particulates (Wear Debris Analysis).",
          "Check bearing seal integrity on non-drive end.",
        ];

  return (
    <div className="flex-1 flex flex-col bg-white dark:bg-card-dark relative">
      <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">

        {/* ── Header ── */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-primary rounded-2xl flex items-center justify-center text-white shadow-xl shadow-primary/30">
              {isActuallyLoading && !rawAnswer ? (
                <span className="w-5 h-5 rounded-full border-2 border-white border-t-transparent animate-spin" />
              ) : (
                <span className="material-symbols-rounded text-2xl">auto_awesome</span>
              )}
            </div>
            <div>
              <h2 className="text-2xl font-bold">Sentinel AI Diagnosis</h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm">
                {isActuallyLoading && !rawAnswer ? (
                  <span className="text-primary animate-pulse">
                    Fetching latest diagnosis...
                  </span>
                ) : notifTimestamp ? (
                  <>Last updated: <span className="text-green-500 font-semibold">{notifTimestamp}</span></>
                ) : (
                  <>Confidence Score: <span className="text-green-500 font-bold">94.2%</span></>
                )}
              </p>
            </div>
          </div>

          <div className="bg-slate-100 dark:bg-slate-800 p-1 rounded-full flex items-center gap-1">
            <span className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-500">
              RAG SOURCES
            </span>
            {sources.length > 0 ? (
              sources.slice(0, 2).map((s, i) => (
                <button
                  key={i}
                  className="px-3 py-1 rounded-full text-xs font-semibold bg-white dark:bg-slate-700 shadow-sm text-primary truncate max-w-[120px]"
                >
                  {s.file?.replace(".pdf", "").slice(0, 15)}…
                </button>
              ))
            ) : (
              <>
                <button className="px-3 py-1 rounded-full text-xs font-semibold bg-white dark:bg-slate-700 shadow-sm text-primary">
                  SKF-M-2023
                </button>
                <button className="px-3 py-1 rounded-full text-xs font-semibold text-slate-500">
                  ISO-10816
                </button>
              </>
            )}
          </div>
        </div>

        {/* ── Machine ID selector ── */}
        <div className="flex items-center gap-3 mb-6 p-4 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <span className="material-symbols-rounded text-slate-400 text-lg">memory</span>
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider whitespace-nowrap">
            Machine ID
          </span>
          <input
            className="flex-1 bg-white dark:bg-card-dark border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-1.5 text-sm font-mono focus:ring-2 focus:ring-primary focus:outline-none"
            value={machineInput}
            onChange={(e) => setMachineInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleMachineChange()}
            placeholder="e.g. machine-81"
          />
          <button
            onClick={handleMachineChange}
            disabled={!machineInput.trim() || machineInput.trim() === machineId}
            className="px-4 py-1.5 rounded-xl bg-primary text-white text-xs font-bold disabled:opacity-40 disabled:cursor-not-allowed hover:bg-primary/90 transition-colors"
          >
            Apply
          </button>
          {notifications.length > 0 && (
            <div className="flex items-center gap-1">
              <span className="px-2 py-1 rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 text-xs font-bold whitespace-nowrap">
                {notifications.length} event{notifications.length !== 1 ? "s" : ""}
              </span>
              <button
                onClick={clearNotifications}
                title="Clear notifications"
                className="w-5 h-5 flex items-center justify-center rounded-full bg-slate-200 dark:bg-slate-700 hover:bg-red-100 hover:text-red-500 text-slate-500 transition-colors text-xs font-bold"
              >
                ✕
              </button>
            </div>
          )}
        </div>

        {/* ── Root cause + urgency ── */}
        <div className="grid grid-cols-2 gap-6 mb-8">
          <div className="p-6 rounded-3xl bg-primary/5 border border-primary/10">
            <h3 className="text-xs font-bold text-primary uppercase tracking-widest mb-4">
              Primary Root Cause
            </h3>
            {isActuallyLoading && !rawAnswer ? (
              <div className="space-y-2">
                <div className="h-4 bg-primary/10 rounded animate-pulse w-full" />
                <div className="h-4 bg-primary/10 rounded animate-pulse w-3/4" />
                <div className="h-4 bg-primary/10 rounded animate-pulse w-1/2" />
              </div>
            ) : (
              <p className="text-lg font-semibold leading-relaxed">
                {displayRootCause}
              </p>
            )}
          </div>

          <div className="p-6 rounded-3xl bg-secondary/10 border border-secondary/20">
            <h3 className="text-xs font-bold text-secondary uppercase tracking-widest mb-4">
              Urgency Assessment
            </h3>
            {isActuallyLoading && !rawAnswer ? (
              <div className="space-y-2">
                <div className="h-4 bg-secondary/10 rounded animate-pulse w-full" />
                <div className="h-4 bg-secondary/10 rounded animate-pulse w-2/3" />
              </div>
            ) : (
              <p className="text-lg font-semibold leading-relaxed">
                {displayFaultCause}
              </p>
            )}
          </div>
        </div>

        {/* ── Recommendations ── */}
        <div className="space-y-6">
          <div className="flex items-start gap-4">
            <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center flex-shrink-0">
              <span className="material-symbols-rounded text-sm text-slate-500">
                format_list_bulleted
              </span>
            </div>
            <div className="space-y-4 flex-1">
              <h4 className="font-bold text-lg">Actionable Recommendations</h4>
              {isActuallyLoading && !rawAnswer ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className="h-4 bg-slate-100 dark:bg-slate-800 rounded animate-pulse"
                      style={{ width: `${60 + i * 12}%` }}
                    />
                  ))}
                </div>
              ) : (
                <ul className="space-y-3">
                  {displayRecommendations.map((r, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-3 text-slate-600 dark:text-slate-300"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-primary mt-2 flex-shrink-0" />
                      {r}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* Citation */}
          <div className="flex items-start gap-4 p-4 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0 text-blue-600 dark:text-blue-400">
              <span className="material-symbols-rounded text-sm">menu_book</span>
            </div>
            <div className="flex-1">
              {citation ? (
                <>
                  <h4 className="text-sm font-bold mb-1">{citation.title}</h4>
                  <p className="text-xs text-slate-500 leading-relaxed italic">
                    &quot;{citation.text}...&quot;
                  </p>
                </>
              ) : latestNotif ? (
                <>
                  <h4 className="text-sm font-bold mb-1">
                    Event ID: {latestNotif.message_id?.slice(0, 8)}…
                  </h4>
                  <p className="text-xs text-slate-500 leading-relaxed italic">
                    &quot;{latestNotif.fault_cause?.slice(0, 220)}...&quot;
                  </p>
                </>
              ) : (
                <>
                  <h4 className="text-sm font-bold mb-1">
                    Citing: SKF Rolling Bearing Manual Sec. 7.4
                  </h4>
                  <p className="text-xs text-slate-500 leading-relaxed italic">
                    &quot;Vibration signatures exhibiting high-frequency modulation at
                    the Ball Pass Frequency Inner race (BPFI) typically indicate
                    fatigue spalling...&quot;
                  </p>
                </>
              )}
            </div>
          </div>

          {/* Error state */}
          {(error || notificationsError) && (
            <div className="p-4 rounded-2xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 text-sm flex items-center gap-3">
              <span className="material-symbols-rounded text-lg">error</span>
              <span>{error || notificationsError}</span>
              <button
                onClick={() => fetchNotifications(machineId)}
                className="ml-auto underline text-xs"
              >
                Retry
              </button>
            </div>
          )}

          {/* Follow-up chat history */}
          {chatHistory.length > 0 && (
            <div className="space-y-3 pt-2">
              <h4 className="font-bold text-sm text-slate-500 uppercase tracking-wider">
                Follow-up
              </h4>
              {chatHistory.map((msg, i) => (
                <div
                  key={i}
                  className={
                    "flex gap-3 " +
                    (msg.role === "user" ? "justify-end" : "justify-start")
                  }
                >
                  <div
                    className={
                      "max-w-[80%] px-4 py-3 rounded-2xl text-sm " +
                      (msg.role === "user"
                        ? "bg-primary text-white rounded-br-sm"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-bl-sm")
                    }
                  >
                    {msg.text}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex gap-3 justify-start">
                  <div className="px-4 py-3 rounded-2xl bg-slate-100 dark:bg-slate-800 rounded-bl-sm">
                    <span className="flex gap-1">
                      <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "300ms" }} />
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Input bar ── */}
      <div className="p-6 bg-slate-50 dark:bg-slate-900/50 border-t border-slate-200 dark:border-slate-800">
        <div className="max-w-3xl mx-auto">
          <div className="mb-4 flex gap-2 overflow-x-auto pb-2 no-scrollbar">
            {QUICK_ACTIONS.map((qa) => (
              <button
                key={qa.label}
                onClick={() => handleSend(qa)}
                disabled={isLoading}
                className="whitespace-nowrap px-4 py-1.5 rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-card-dark text-xs font-medium hover:border-primary transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {qa.label}
              </button>
            ))}
          </div>

          <div className="relative">
            <input
              className="w-full bg-white dark:bg-card-dark border-none rounded-2xl py-4 px-6 pr-16 shadow-lg shadow-black/5 focus:ring-2 focus:ring-primary focus:outline-none dark:text-white transition-shadow disabled:opacity-60"
              placeholder="Ask follow-up questions for root cause analysis..."
              type="text"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
            />
            <button
              className="absolute right-3 top-2 bottom-2 aspect-square bg-primary text-white rounded-xl flex items-center justify-center hover:scale-105 transition-transform disabled:opacity-40 disabled:cursor-not-allowed disabled:scale-100"
              onClick={() => handleSend(null)}
              disabled={isLoading || !q.trim()}
              aria-label="Send"
            >
              {isLoading ? (
                <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
              ) : (
                <span className="material-symbols-rounded">send</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
