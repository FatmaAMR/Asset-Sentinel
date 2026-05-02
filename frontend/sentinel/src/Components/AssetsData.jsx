export default function AssetsData() {
  return (
    <section className="grid grid-cols-3 gap-6 mb-10">
      <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
        <h4 className="text-xs font-bold text-slate-400 uppercase mb-1">Asset ID</h4>
        <p className="text-md font-bold text-slate-900">TURB-04-NORTH-B2</p>
      </div>
      <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
        <h4 className="text-xs font-bold text-slate-400 uppercase mb-1">Location</h4>
        <p className="text-md font-bold text-slate-900">Plant Alpha / Sector 7</p>
      </div>
      <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
        <h4 className="text-xs font-bold text-slate-400 uppercase mb-1">Last Inspection</h4>
        <p className="text-md font-bold text-slate-900">Sept 12, 2023</p>
      </div>

    </section>
  );
}