import { useEffect } from 'react';
import useAssetStore from '../stores/assetStore';

const statusConfig = {
  Critical: {
    badge: 'bg-red-50 text-failure border border-red-100',
    icon: 'flash_on',
    iconBg: 'bg-red-50 text-failure',
    metricsColor: 'text-failure font-semibold',
  },
  Warning: {
    badge: 'bg-amber-50 text-warning border border-amber-100',
    icon: 'precision_manufacturing',
    iconBg: 'bg-amber-50 text-warning',
    metricsColor: 'text-warning font-semibold',
  },
  Normal: {
    badge: 'bg-emerald-50 text-normal border border-emerald-100',
    icon: 'settings_input_component',
    iconBg: 'bg-emerald-50 text-normal',
    metricsColor: 'text-normal font-semibold',
  },
};

export default function AssetsCard() {
  const { factorySummary, loading, fetchFactorySummary } = useAssetStore();

  useEffect(() => {
    fetchFactorySummary();
  }, []);

  if (loading) return <p className="text-muted text-sm">Loading machines...</p>;

  const machines = factorySummary?.machines_details ?? [];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {machines.map((machine) => {
        const config = statusConfig[machine.status] ?? statusConfig.Normal;
        return (
          <div
            key={machine.machine_id}
            className="bg-white p-6 rounded-2xl border border-slate-100 shadow-[0_2px_12px_rgba(15,23,42,0.03)] hover:shadow-[0_4px_20px_rgba(15,23,42,0.06)] transition-all duration-200"
          >
            {/* Header: Soft colored icon box and clean tag */}
            <div className="flex justify-between items-center mb-5">
              <div className={`p-2 rounded-xl ${config.iconBg}`}>
                <span className="material-icons-round text-xl block">{config.icon}</span>
              </div>
              <span className={`${config.badge} text-[10px] font-bold px-2.5 py-1 rounded-lg uppercase tracking-wider`}>
                {machine.status}
              </span>
            </div>

            {/* Typography */}
            <h4 className="font-bold text-lg text-light tracking-tight mb-0.5">{machine.machine_id}</h4>
            <p className="text-xs text-muted mb-5">RUL: <span className="font-medium text-light">{machine.current_rul_days} days</span></p>
            
            {/* Stats Dividers */}
            <div className="space-y-3 pt-3 border-t border-slate-100">
              <div className="flex justify-between items-center text-xs">
                <span className="text-muted">Vibration RMS</span>
                <span className={`font-mono ${config.metricsColor}`}>
                  {machine.avg_vibration} mm/s
                </span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-muted">Avg Temperature</span>
                <span className="font-mono font-semibold text-light">
                  {machine.avg_temperature}°C
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}