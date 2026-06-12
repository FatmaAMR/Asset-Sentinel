import { useEffect } from 'react';
import useAssetStore from '../stores/assetStore';

const MAX_VISIBLE = 5;

const severityConfig = {
  Critical: {
    border: 'border-failure',
    bg: 'bg-failure/5',
    badge: 'text-failure',
    label: 'CRITICAL BREACH',
    showActions: true,
  },
  Warning: {
    border: 'border-warning',
    bg: 'bg-warning/5',
    badge: 'text-warning',
    label: 'WARNING',
    showActions: false,
  },
  Scheduled: {
    border: 'border-blue-400',
    bg: 'bg-blue-50',
    badge: 'text-blue-600',
    label: 'SCHEDULED',
    showActions: false,
  },
};

function timeAgo(timestamp) {
  const diff = Math.floor((Date.now() - new Date(timestamp)) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

export default function AlertsSidebar() {
  const { alerts, loading, fetchAlerts } = useAssetStore();

  useEffect(() => {
    fetchAlerts();
  }, []);

  const criticalCount = alerts.filter((a) => a.severity === 'Critical').length;
  const visible = alerts.slice(0, MAX_VISIBLE);
  const overflow = alerts.length - MAX_VISIBLE;

  return (
    <div className="space-y-8">
      <div className="bg-cards-light rounded-3xl p-6 border border-gray-100 shadow-sm flex flex-col">
        <h3 className="text-lg font-bold mb-6 flex items-center justify-between">
          Instant Alerts
          {criticalCount > 0 && (
            <span className="text-[10px] bg-failure text-white px-2 py-0.5 rounded-full">
              {criticalCount} New
            </span>
          )}
        </h3>

        <div className="space-y-4 flex-grow">
          {loading ? (
            <p className="text-slate-400 text-sm">Loading alerts...</p>
          ) : alerts.length === 0 ? (
            <p className="text-slate-400 text-sm">No active alerts</p>
          ) : (
            <>
              {visible.map((alert) => {
                const config = severityConfig[alert.severity] ?? {
                  border: 'border-gray-300',
                  bg: 'bg-gray-50',
                  badge: 'text-slate-500',
                  label: alert.severity?.toUpperCase() ?? 'ALERT',
                  showActions: false,
                };
                return (
                  <div
                    key={alert.alert_id}
                    className={`p-4 ${config.bg} border-l-4 ${config.border} rounded-xl`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className={`text-xs font-bold ${config.badge}`}>
                        {config.label}
                      </span>
                      <span className="text-[10px] text-slate-400">
                        {timeAgo(alert.timestamp)}
                      </span>
                    </div>
                    <p className="text-sm font-medium leading-snug text-slate-600">
                      {alert.message}
                    </p>
                    {config.showActions && (
                      <div className="mt-3 flex gap-2">
                        <button className="text-[10px] font-bold bg-failure text-white px-3 py-1.5 rounded-lg">
                          AI Diagnosis
                        </button>
                        <button className="text-[10px] font-bold bg-white px-3 py-1.5 rounded-lg border border-gray-200">
                          Ignore
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
              {overflow > 0 && (
                <p className="text-center text-xs text-slate-400 pt-1">
                  +{overflow} more alert{overflow > 1 ? 's' : ''} — check Reports for full list
                </p>
              )}
            </>
          )}
        </div>

        <div className="mt-8 pt-6 border-t border-gray-100 space-y-3">
          <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2">
            Quick Actions
          </p>
          <button className="w-full flex items-center justify-between p-3 rounded-2xl bg-slate-100 text-slate-600 font-semibold text-sm hover:bg-slate-200 transition-colors">
            Dismiss All Non-Critical
            <span className="material-icons-round text-lg">done_all</span>
          </button>
        </div>
      </div>

      

    </div>
  );
}