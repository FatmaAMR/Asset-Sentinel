export default function AssetsCard() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="bg-cards-light p-5 rounded-3xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
        <div className="flex justify-between items-start mb-4">
          <div className="p-3 bg-normal/10 rounded-2xl">
            <span className="material-icons-round text-normal">settings_input_component</span>
          </div>
          <span className="bg-normal/10 text-normal text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-wider">Optimal</span>
        </div>
        <h4 className="font-bold text-lg">Turbine Unit 04-B</h4>
        <p className="text-xs text-slate-500 mb-6">Sector: Wind Farm Alpha</p>
        <div className="space-y-3">
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">Vibration RMS</span>
            <span className="font-mono font-medium">1.2 mm/s</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">Peak Frequency</span>
            <span className="font-mono font-medium">14.5 Hz</span>
          </div>
        </div>
      </div>
      <div className="bg-cards-light p-5 rounded-3xl border-2 border-warning/30 shadow-sm hover:shadow-md transition-shadow">
        <div className="flex justify-between items-start mb-4">
          <div className="p-3 bg-warning/10 rounded-2xl">
            <span className="material-icons-round text-warning">precision_manufacturing</span>
          </div>
          <span className="bg-warning/10 text-warning text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-wider">Warning</span>
        </div>
        <h4 className="font-bold text-lg">Centrifugal Pump C7</h4>
        <p className="text-xs text-slate-500 mb-6">Sector: Water Treatment</p>
        <div className="space-y-3">
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">Vibration RMS</span>
            <span className="font-mono font-medium text-warning">4.8 mm/s</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">Peak Frequency</span>
            <span className="font-mono font-medium">52.1 Hz</span>
          </div>
        </div>
      </div>
      <div className="bg-cards-light p-5 rounded-3xl border-2 border-failure/30 shadow-sm hover:shadow-md transition-shadow">
        <div className="flex justify-between items-start mb-4">
          <div className="p-3 bg-failure/10 rounded-2xl">
            <span className="material-icons-round text-failure">flash_on</span>
          </div>
          <span className="bg-failure/10 text-failure text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-wider">Critical</span>
        </div>
        <h4 className="font-bold text-lg">Induction Motor 12</h4>
        <p className="text-xs text-slate-500 mb-6">Sector: Assembly Line 2</p>
        <div className="space-y-3">
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">Vibration RMS</span>
            <span className="font-mono font-medium text-failure">12.4 mm/s</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">Peak Frequency</span>
            <span className="font-mono font-medium">84.0 Hz</span>
          </div>
        </div>
      </div>

    </div>
  );
}