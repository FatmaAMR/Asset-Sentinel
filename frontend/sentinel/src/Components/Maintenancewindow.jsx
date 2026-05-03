export default function Maintenancewindow() {
  return (
    <section className="mt-12 bg-amber-50 border border-amber-200 p-8 rounded-3xl">
      <div className="flex items-start gap-6">
        <div className="w-12 h-12 bg-amber-100 text-amber-600 rounded-2xl flex items-center justify-center shrink-0">
          <span className="material-icons-round">warning_amber</span>
        </div>
        <div>
          <h3 className="text-lg font-bold text-amber-900 mb-1">
            Upcoming Maintenance Window
          </h3>
          <p className="text-amber-800/70">
            Automatic system optimization is scheduled for 02:00 AM UTC. Inference might experience momentary latency increases during indexing.
          </p>
        </div>
        <button className="ml-auto text-sm font-bold text-amber-900 hover:underline shrink-0">
          Dismiss
        </button>
      </div>
    </section>
  );
}