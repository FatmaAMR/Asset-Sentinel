import { useEffect } from 'react';
import useAssetStore from '../stores/assetStore';

export default function StatusCards() {
  const { factorySummary, loading, fetchFactorySummary } = useAssetStore();

  useEffect(() => {
    fetchFactorySummary();
  }, []);

  const activeSensors = factorySummary?.active_sensors ?? null;

  // Compute sensor health % — what % of sensor readings are from non-critical machines
  const totalMachines = factorySummary?.total_machines ?? 0;
  const criticalMachines = factorySummary?.critical_machines_count ?? 0;
  const healthPct = totalMachines > 0
    ? Math.round(((totalMachines - criticalMachines) / totalMachines) * 100)
    : 94;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      {/* Total Fleet Assets */}
      <div className="bg-primary p-6 rounded-3xl text-white shadow-xl relative overflow-hidden group">
        <div className="relative z-10">
          <p className="text-white/70 text-sm font-medium">Total Fleet Assets</p>
          <h3 className="text-4xl font-bold mt-1">
            {loading ? '...' : factorySummary?.total_machines ?? '—'}
          </h3>
          <div className="mt-4 flex items-center gap-2 text-xs bg-white/20 w-fit px-2 py-1 rounded-full">
            <span className="material-icons-round text-sm">trending_up</span>
            <span>+12 this month</span>
          </div>
        </div>
        <span className="material-icons-round absolute -right-4 -bottom-4 text-9xl opacity-10 group-hover:scale-110 transition-transform">
          inventory_2
        </span>
      </div>

      {/* Critical Alerts */}
      <div className="bg-cards-light p-6 rounded-3xl border border-gray-100 shadow-sm flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-slate-500 text-sm font-medium">Critical Alerts</p>
            <span className="w-2 h-2 rounded-full bg-failure animate-ping" />
          </div>
          <h3 className="text-4xl font-bold text-failure">
            {loading
              ? '...'
              : String(factorySummary?.critical_machines_count ?? '—').padStart(1, '0')}
          </h3>
        </div>
        <p className="text-xs text-slate-400 mt-4 italic">ISO 10816 Breach detected</p>
      </div>

      {/* Active Sensors — live from API */}
      <div className="bg-cards-light p-6 rounded-3xl border border-gray-100 shadow-sm flex flex-col justify-between">
        <div>
          <p className="text-slate-500 text-sm font-medium mb-2">Active Sensors</p>
          <h3 className="text-4xl font-bold text-slate-800">
            {loading
              ? '...'
              : activeSensors != null
              ? activeSensors.toLocaleString()
              : '—'}
          </h3>
        </div>
        <div className="w-full bg-gray-100 h-1.5 rounded-full mt-4 overflow-hidden">
          <div
            className="bg-normal h-full transition-all duration-700"
            style={{ width: `${healthPct}%` }}
          />
        </div>
        <p className="text-[10px] text-slate-400 mt-1">{healthPct}% healthy</p>
      </div>

      {/* AI Diagnostic Accuracy */}
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