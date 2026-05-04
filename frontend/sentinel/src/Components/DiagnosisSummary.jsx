export default function DiagnosisSummary() {
  return (
    <section className="mb-10">
      <div className="flex items-center gap-2 mb-4">
        <span className="material-icons-round text-primary">psychology</span>
        <h3 className="text-lg font-bold text-slate-900">
          Sentinel AI Diagnostic Summary
        </h3>
      </div>
      <div className="bg-primary/5 p-6 rounded-xl border border-primary/20 relative overflow-hidden">
        <div className="absolute top-0 right-0 opacity-5 translate-x-10 -translate-y-10">
          <span className="material-icons-round text-[120px]">auto_awesome</span>
        </div>

        <p className="text-slate-800 leading-relaxed font-medium">
          Internal analysis of vibration spectrum sensor{" "}
          <span className="text-primary font-bold">V-NODE-04</span>{" "}
          indicates a high-probability of{" "}
          <span className="text-primary font-bold">94.2%</span>{" "}
          of{" "}
          <span className="font-bold underline decoration-primary/30">
            Bearing Inner Race Wear
          </span>{" "}
          in the primary drive housing. The RAG system detected frequency
          peaks matching the BPFI (Ball Pass Frequency Inner Race) harmonics.
          Immediate replacement is recommended to prevent cascading shaft
          misalignment.
        </p>

      </div>
    </section>
  );
}