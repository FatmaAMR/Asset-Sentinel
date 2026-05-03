export default function SystemConfig() {
  return (
    <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
      <div className="max-w-2xl">
        <h1 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight">
          System Configuration & Health
        </h1>
        <p className="text-slate-500 text-lg">
          Manage your predictive maintenance engine, adjust inference models, and monitor hardware performance in real-time.
        </p>
      </div>
      <button className="px-6 py-3 bg-slate-900 text-white font-semibold rounded-2xl hover:opacity-90 transition-all flex items-center gap-2 w-fit">
        <span className="material-icons-round text-[20px]">refresh</span>
        Refresh System
      </button>

    </div>
  );
}