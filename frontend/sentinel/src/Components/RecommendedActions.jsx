import { useState } from "react";

export default function RecommendedActions() {
  const [checked, setChecked] = useState([false, false, false, false]);

  function toggle(index) {
    setChecked(checked.map((c, i) => (i === index ? !c : c)));
  }

  return (
    <section className="mb-10">
      <div className="flex items-center gap-2 mb-4">
        <span className="material-icons-round text-primary">task_alt</span>
        <h3 className="text-lg font-bold text-slate-900">
          Recommended Remediation Action Plan
        </h3>
      </div>
      <div className="space-y-3">

        <div
          onClick={() => toggle(0)}
          className="flex items-center gap-4 p-4 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors"
        >
          <div className={`w-6 h-6 rounded border-2 flex-shrink-0 flex items-center justify-center transition-colors ${checked[0] ? "bg-primary border-primary" : "border-slate-300"}`}>
            {checked[0] && <span className="material-icons-round text-white text-sm">check</span>}
          </div>
          <span className={`font-medium ${checked[0] ? "line-through text-slate-400" : "text-slate-800"}`}>
            Isolate Turbine-04 from the north-grid substation prior to inspection.
          </span>
        </div>

        <div
          onClick={() => toggle(1)}
          className="flex items-center gap-4 p-4 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors"
        >
          <div className={`w-6 h-6 rounded border-2 flex-shrink-0 flex items-center justify-center transition-colors ${checked[1] ? "bg-primary border-primary" : "border-slate-300"}`}>
            {checked[1] && <span className="material-icons-round text-white text-sm">check</span>}
          </div>
          <span className={`font-medium ${checked[1] ? "line-through text-slate-400" : "text-slate-800"}`}>
            Dismantle drive-end housing and inspect bearing 3422-C3 for inner race flaking.
          </span>
        </div>

        <div
          onClick={() => toggle(2)}
          className="flex items-center gap-4 p-4 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors"
        >
          <div className={`w-6 h-6 rounded border-2 flex-shrink-0 flex items-center justify-center transition-colors ${checked[2] ? "bg-primary border-primary" : "border-slate-300"}`}>
            {checked[2] && <span className="material-icons-round text-white text-sm">check</span>}
          </div>
          <span className={`font-medium ${checked[2] ? "line-through text-slate-400" : "text-slate-800"}`}>
            Verify lubrication purity; check for metallic particulates in current grease sample.
          </span>
        </div>

        <div
          onClick={() => toggle(3)}
          className="flex items-center gap-4 p-4 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors"
        >
          <div className={`w-6 h-6 rounded border-2 flex-shrink-0 flex items-center justify-center transition-colors ${checked[3] ? "bg-primary border-primary" : "border-slate-300"}`}>
            {checked[3] && <span className="material-icons-round text-white text-sm">check</span>}
          </div>
          <span className={`font-medium ${checked[3] ? "line-through text-slate-400" : "text-slate-800"}`}>
            Re-calibrate vibration node V-NODE-04 post-repair to baseline.
          </span>
        </div>

      </div>
    </section>
  );
}