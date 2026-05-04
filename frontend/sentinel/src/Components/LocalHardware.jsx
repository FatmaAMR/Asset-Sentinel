/* eslint-disable react/prop-types */
function GaugeRing({ percentage, color, dashoffset }) {
  return (
    <div className="relative w-24 h-24">
      <svg className="w-full h-full transform -rotate-90">
        <circle
          className="text-slate-100"
          cx="48" cy="48"
          fill="transparent"
          r="40"
          stroke="currentColor"
          strokeWidth="8"
        />
        <circle
          className={`${color}`}
          cx="48" cy="48"
          fill="transparent"
          r="40"
          stroke="currentColor"
          strokeDasharray="251.2"
          strokeDashoffset={dashoffset}
          strokeLinecap="round"
          strokeWidth="8"
          style={{ transition: "stroke-dashoffset 0.5s ease-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center font-bold text-xl">
        {percentage}<span className="text-[10px] text-slate-400">%</span>
      </div>
    </div>
  );
}

export default function LocalHardware() {
  return (
    <section className="bg-cards-light p-8 rounded-3xl border border-slate-200 shadow-sm sticky top-28">
      <div className="flex items-center justify-between mb-8">
        <h3 className="text-xl font-bold">Local Hardware</h3>
        <span className="flex h-2 w-2 rounded-full bg-normal animate-pulse" />
      </div>
      <div className="space-y-10">
        <div className="flex items-center gap-6">
          <GaugeRing percentage={76} color="text-primary" dashoffset={60} />
          <div>
            <h5 className="font-bold text-lg">GPU Load</h5>
            <p className="text-sm text-slate-500">NVIDIA RTX 4090</p>
            <div className="flex gap-2 mt-1">
              <span className="text-[10px] font-bold px-1.5 py-0.5 bg-orange-100 text-orange-600 rounded">
                64°C
              </span>
              <span className="text-[10px] font-bold px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded">
                24GB VRAM
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <GaugeRing percentage={44} color="text-amber-400" dashoffset={140} />
          <div>
            <h5 className="font-bold text-lg">System RAM</h5>
            <p className="text-sm text-slate-500">64GB DDR5</p>
            <p className="text-[11px] text-slate-400 mt-1 uppercase font-semibold">28.1GB Used</p>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <GaugeRing percentage={21} color="text-emerald-500" dashoffset={200} />
          <div>
            <h5 className="font-bold text-lg">CPU Utilization</h5>
            <p className="text-sm text-slate-500">Intel i9-14900K</p>
            <p className="text-[11px] text-slate-400 mt-1 uppercase font-semibold">24 Cores Active</p>
          </div>
        </div>

      </div>
      <div className="mt-12 pt-8 border-t border-slate-100">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-medium text-slate-500">Inference Speed</span>
          <span className="text-sm font-bold text-primary">42.4 t/s</span>
        </div>
        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
          <div className="bg-primary h-full w-[85%] rounded-full" />
        </div>
      </div>

    </section>
  );
}