import { useEffect } from 'react';
import useAssetStore from '../stores/assetStore';

const statusConfig = {
  Critical: {
    border: 'border-2 border-failure/30',
    badge: 'bg-failure/10 text-failure',
    icon: 'flash_on',
    iconBg: 'bg-failure/10',
    iconColor: 'text-failure',
    vibrationColor: 'text-failure',
  },
  Warning: {
    border: 'border-2 border-warning/30',
    badge: 'bg-warning/10 text-warning',
    icon: 'precision_manufacturing',
    iconBg: 'bg-warning/10',
    iconColor: 'text-warning',
    vibrationColor: 'text-warning',
  },
  Normal: {
    border: 'border border-gray-100',
    badge: 'bg-normal/10 text-normal',
    icon: 'settings_input_component',
    iconBg: 'bg-normal/10',
    iconColor: 'text-normal',
    vibrationColor: 'font-medium',
  },
};

export default function AssetsCard() {
  const { factorySummary, loading, fetchFactorySummary } = useAssetStore();

  useEffect(() => {
    fetchFactorySummary();
  }, []);

  if (loading) return <p className="text-slate-400 text-sm">Loading machines...</p>;

  const machines = factorySummary?.machines_details ?? [];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {machines.map((machine) => {
        const config = statusConfig[machine.status] ?? statusConfig.Normal;
        return (
          <div
            key={machine.machine_id}
            className={`bg-cards-light p-5 rounded-3xl shadow-sm hover:shadow-md transition-shadow ${config.border}`}
          >
            <div className="flex justify-between items-start mb-4">
              <div className={`p-3 ${config.iconBg} rounded-2xl`}>
                <span className={`material-icons-round ${config.iconColor}`}>{config.icon}</span>
              </div>
              <span className={`${config.badge} text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-wider`}>
                {machine.status}
              </span>
            </div>
            <h4 className="font-bold text-lg">{machine.machine_id}</h4>
            <p className="text-xs text-slate-500 mb-6">RUL: {machine.current_rul_days} days</p>
            <div className="space-y-3">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Vibration RMS</span>
                <span className={`font-mono font-medium ${config.vibrationColor}`}>
                  {machine.avg_vibration} mm/s
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Avg Temperature</span>
                <span className="font-mono font-medium">{machine.avg_temperature}°C</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}