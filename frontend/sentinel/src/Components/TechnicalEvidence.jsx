export default function TechnicalEvidence() {
  return (
    <section className="mb-10">
      <div className="flex items-center gap-2 mb-4">
        <span className="material-icons-round text-primary">query_stats</span>
        <h3 className="text-lg font-bold text-slate-900">
          Technical Evidence & RAG Verification
        </h3>
      </div>

      <div className="grid grid-cols-2 gap-8">
        <div className="space-y-4">
          <div className="p-4 border border-slate-200 rounded-lg">
            <h4 className="text-xs font-bold text-slate-500 uppercase mb-3">
              Vibration Velocity (RMS)
            </h4>
            <div className="h-24 w-full flex items-end gap-1 rounded p-2"
              style={{ background: "linear-gradient(180deg, rgba(127, 19, 236, 0.1) 0%, rgba(127, 19, 236, 0) 100%)" }}
            >
              <div className="flex-1 bg-slate-300 rounded-t-sm" style={{ height: "25%" }} />
              <div className="flex-1 bg-slate-300 rounded-t-sm" style={{ height: "33%" }} />
              <div className="flex-1 bg-slate-300 rounded-t-sm" style={{ height: "25%" }} />
              <div className="flex-1 bg-slate-300 rounded-t-sm" style={{ height: "50%" }} />
              <div className="flex-1 bg-primary rounded-t-sm" style={{ height: "75%" }} />
              <div className="flex-1 bg-primary rounded-t-sm" style={{ height: "100%" }} />
              <div className="flex-1 bg-primary rounded-t-sm" style={{ height: "83%" }} />
              <div className="flex-1 bg-primary rounded-t-sm" style={{ height: "75%" }} />
              <div className="flex-1 bg-primary rounded-t-sm" style={{ height: "100%" }} />
            </div>
            <div className="flex justify-between mt-2 text-[10px] font-bold text-slate-400">
              <span>T-48H</span>
              <span>PEAK ANOMALY</span>
              <span>CURRENT</span>
            </div>
          </div>
        </div>
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-slate-500 uppercase">
            Knowledge Base Citations
          </h4>
          <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg border border-slate-100">
            <div className="w-10 h-10 bg-cards-light border border-slate-200 flex items-center justify-center shrink-0">
              <span className="material-icons-round text-slate-400 text-sm">book</span>
            </div>
            <div>
              <p className="text-xs font-bold text-slate-900 leading-tight">
                ISO 10816-3:2017
              </p>
              <p className="text-[10px] text-slate-500 italic leading-tight">
                Mechanical vibration — Eval. of machine vibration by measurements on non-rotating parts.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg border border-slate-100">
            <div className="w-10 h-10 bg-cards-light border border-slate-200 flex items-center justify-center shrink-0">
              <span className="material-icons-round text-slate-400 text-sm">menu_book</span>
            </div>
            <div>
              <p className="text-xs font-bold text-slate-900 leading-tight">
                SKF Rolling Bearings Manual
              </p>
              <p className="text-[10px] text-slate-500 italic leading-tight">
                Section 12.4: Diagnosis of rolling bearing damage using frequency analysis.
              </p>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}