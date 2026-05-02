export default function StatusCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div className="bg-primary p-6 rounded-3xl text-white shadow-xl relative overflow-hidden group">
        <div className="relative z-10">
          <p className="text-white/70 text-sm font-medium">Total Fleet Assets</p>
          <h3 className="text-4xl font-bold mt-1">1,284</h3>
          <div className="mt-4 flex items-center gap-2 text-xs bg-white/20 w-fit px-2 py-1 rounded-full">
            <span className="material-icons-round text-sm">trending_up</span>
            <span>+12 this month</span>
          </div>
        </div>
        <span className="material-icons-round absolute -right-4 -bottom-4 text-9xl opacity-10 group-hover:scale-110 transition-transform">inventory_2</span>
      </div>
      <div className="bg-cards-light p-6 rounded-3xl border border-gray-100 shadow-sm flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-slate-500 text-sm font-medium">Critical Alerts</p>
            <span className="w-2 h-2 rounded-full bg-failure animate-ping" />
          </div>
          <h3 className="text-4xl font-bold text-failure">03</h3>
        </div>
        <p className="text-xs text-slate-400 mt-4 italic">ISO 10816 Breach detected</p>
      </div>
      <div className="bg-cards-light p-6 rounded-3xl border border-gray-100 shadow-sm flex flex-col justify-between">
        <div>
          <p className="text-slate-500 text-sm font-medium mb-2">Active Sensors</p>
          <h3 className="text-4xl font-bold text-slate-800">8,942</h3>
        </div>
        <div className="w-full bg-gray-100 h-1.5 rounded-full mt-4 overflow-hidden">
          <div className="bg-normal h-full w-[94%]" />
        </div>
      </div>
      <div className="bg-cards-light p-6 rounded-3xl border border-gray-100 shadow-sm flex flex-col justify-between">
        <div>
          <p className="text-slate-500 text-sm font-medium mb-2">AI Diagnostic Accuracy</p>
          <h3 className="text-4xl font-bold text-primary">99.8%</h3>
        </div>
        <p className="text-xs text-slate-400 mt-4">Local Llama-3-70B Active</p>
      </div>

    </div>
  );
}