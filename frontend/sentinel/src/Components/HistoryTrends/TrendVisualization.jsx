export default function TrendVisualization() {
  return (
    <section className="bg-white dark:bg-[#1E293B] rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm overflow-hidden">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
        <div>
          <h2 className="text-xl font-bold">Trend Visualization</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Monitoring RMS Velocity (mm/s) across critical nodes
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex bg-slate-100 dark:bg-slate-900 rounded-lg p-1">
            <button className="px-3 py-1.5 text-xs font-medium bg-white dark:bg-slate-800 rounded shadow-sm">
              Vibration
            </button>
            <button className="px-3 py-1.5 text-xs font-medium text-slate-500 hover:text-slate-700 dark:hover:text-slate-200">
              Thermal
            </button>
            <button className="px-3 py-1.5 text-xs font-medium text-slate-500 hover:text-slate-700 dark:hover:text-slate-200">
              Acoustic
            </button>
          </div>

          <button className="p-2 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800">
            <span className="material-icons-round text-lg">download</span>
          </button>
        </div>
      </div>

      <div
        className="relative h-[300px] w-full mt-4 border-b border-l border-slate-200 dark:border-slate-700 flex items-end"
        style={{
          background:
            "linear-gradient(180deg, rgba(124, 58, 237, 0.1) 0%, rgba(124, 58, 237, 0) 100%)",
        }}
      >
        <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-10">
          <div className="border-t border-slate-500 w-full" />
          <div className="border-t border-slate-500 w-full" />
          <div className="border-t border-slate-500 w-full" />
          <div className="border-t border-slate-500 w-full" />
        </div>

        <svg
          className="absolute inset-0 w-full h-full"
          preserveAspectRatio="none"
          viewBox="0 0 1000 300"
        >
          <path
            d="M0,250 L100,240 L200,260 L300,180 L400,200 L500,120 L600,140 L700,80 L800,100 L900,40 L1000,60"
            fill="none"
            stroke="#7C3AED"
            strokeLinecap="round"
            strokeWidth="3"
          />
          <path
            d="M0,280 L100,270 L200,275 L300,260 L400,265 L500,250 L600,255 L700,240 L800,245 L900,230 L1000,235"
            fill="none"
            stroke="#94A3B8"
            strokeDasharray="8,4"
            strokeWidth="2"
          />
          <circle
            className="animate-pulse"
            cx="900"
            cy="40"
            fill="#7C3AED"
            r="6"
          />
          <line
            stroke="#7C3AED"
            strokeDasharray="4,4"
            strokeWidth="1"
            x1="900"
            x2="900"
            y1="40"
            y2="300"
          />
        </svg>

        <div className="absolute left-[88%] top-1 -translate-x-1/2 bg-slate-900 text-white text-[10px] p-2 rounded shadow-xl z-10 hidden md:block">
          <p className="font-bold border-b border-white/20 mb-1 pb-1">
            Oct 24, 14:30
          </p>
          <p>RMS: 12.4 mm/s</p>
          <p className="text-red-400">Deviation: +18%</p>
        </div>
      </div>

      <div className="flex justify-between text-[10px] font-medium text-slate-400 mt-3 px-2">
        <span>Oct 01</span>
        <span>Oct 08</span>
        <span>Oct 15</span>
        <span>Oct 22</span>
        <span>Oct 29</span>
      </div>
    </section>
  );
}
