import { useState } from "react";

const recommendations = [
  "Immediate reduction of turbine load to 60% capacity.",
  "Inspect lubricant for metallic particulates (Wear Debris Analysis).",
  "Check bearing seal integrity on non-drive end.",
];

export default function DiagnosisPanel() {
  const [q, setQ] = useState("");

  return (
    <div className="flex-1 flex flex-col bg-white dark:bg-card-dark relative">
      <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
        <div className="flex items-start justify-between mb-8">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-primary rounded-2xl flex items-center justify-center text-white shadow-xl shadow-primary/30">
              <span className="material-symbols-rounded text-2xl">
                auto_awesome
              </span>
            </div>
            <div>
              <h2 className="text-2xl font-bold">Sentinel AI Diagnosis</h2>
              <p className="text-slate-500 dark:text-slate-400">
                Confidence Score:{" "}
                <span className="text-green-500 font-bold">94.2%</span>
              </p>
            </div>
          </div>

          <div className="bg-slate-100 dark:bg-slate-800 p-1 rounded-full flex items-center gap-1">
            <span className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-500">
              RAG SOURCES
            </span>
            <button className="px-3 py-1 rounded-full text-xs font-semibold bg-white dark:bg-slate-700 shadow-sm text-primary">
              SKF-M-2023
            </button>
            <button className="px-3 py-1 rounded-full text-xs font-semibold text-slate-500">
              ISO-10816
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6 mb-8">
          <div className="p-6 rounded-3xl bg-primary/5 border border-primary/10">
            <h3 className="text-xs font-bold text-primary uppercase tracking-widest mb-4">
              Primary Root Cause
            </h3>
            <p className="text-lg font-semibold leading-relaxed">
              Bearing #4 inner race flaking due to insufficient lubrication
              viscosity at peak operating temperatures.
            </p>
          </div>

          <div className="p-6 rounded-3xl bg-secondary/10 border border-secondary/20">
            <h3 className="text-xs font-bold text-secondary uppercase tracking-widest mb-4">
              Urgency Assessment
            </h3>
            <p className="text-lg font-semibold leading-relaxed">
              Critical: Potential for catastrophic shaft misalignment within{" "}
              <span className="underline decoration-secondary">
                12-24 hours
              </span>
              .
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="flex items-start gap-4">
            <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center flex-shrink-0">
              <span className="material-symbols-rounded text-sm text-slate-500">
                format_list_bulleted
              </span>
            </div>

            <div className="space-y-4">
              <h4 className="font-bold text-lg">Actionable Recommendations</h4>
              <ul className="space-y-3">
                {recommendations.map((r, i) => (
                  <li
                    key={i}
                    className="flex items-center gap-3 text-slate-600 dark:text-slate-300"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="flex items-start gap-4 p-4 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0 text-blue-600 dark:text-blue-400">
              <span className="material-symbols-rounded text-sm">
                menu_book
              </span>
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-bold mb-1">
                Citing: SKF Rolling Bearing Manual Sec. 7.4
              </h4>
              <p className="text-xs text-slate-500 leading-relaxed italic">
                "Vibration signatures exhibiting high-frequency modulation at
                the Ball Pass Frequency Inner race (BPFI) typically indicate
                fatigue spalling..."
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="p-6 bg-slate-50 dark:bg-slate-900/50 border-t border-slate-200 dark:border-slate-800">
        <div className="max-w-3xl mx-auto">
          <div className="mb-4 flex gap-2 overflow-x-auto pb-2 no-scrollbar">
            <button className="whitespace-nowrap px-4 py-1.5 rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-card-dark text-xs font-medium hover:border-primary transition-colors">
              Compare with 2022 overhaul logs
            </button>
            <button className="whitespace-nowrap px-4 py-1.5 rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-card-dark text-xs font-medium hover:border-primary transition-colors">
              Show vibration spectrogram
            </button>
            <button className="whitespace-nowrap px-4 py-1.5 rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-card-dark text-xs font-medium hover:border-primary transition-colors">
              Estimate MTBF
            </button>
          </div>

          <div className="relative">
            <input
              className="w-full bg-white dark:bg-card-dark border-none rounded-2xl py-4 px-6 pr-16 shadow-lg shadow-black/5 focus:ring-2 focus:ring-primary focus:outline-none dark:text-white transition-shadow"
              placeholder="Ask follow-up questions for root cause analysis..."
              type="text"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
            <button
              className="absolute right-3 top-2 bottom-2 aspect-square bg-primary text-white rounded-xl flex items-center justify-center hover:scale-105 transition-transform"
              onClick={() => {
                // placeholder: اAPI
                setQ("");
              }}
              aria-label="Send"
            >
              <span className="material-symbols-rounded">send</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
