import { useEffect, useState } from 'react';
import useAssetStore from '../stores/assetStore';

const PAGE_SIZE = 6;

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
  Scheduled: {
    badge: 'bg-blue-50 text-blue-600 border border-blue-100',
    icon: 'event_available',
    iconBg: 'bg-blue-50 text-blue-600',
    metricsColor: 'text-blue-600 font-semibold',
  },
};

export default function AssetsCard() {
  const { factorySummary, loading, fetchFactorySummary } = useAssetStore();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('All');

  useEffect(() => {
    fetchFactorySummary();
  }, []);

  // Reset to page 1 when filter changes
  useEffect(() => {
    setPage(1);
  }, [statusFilter]);

  const allMachines = factorySummary?.machines_details ?? [];

  const filtered = statusFilter === 'All'
    ? allMachines
    : allMachines.filter((m) => m.status === statusFilter);

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // Status counts for filter pills
  const counts = allMachines.reduce((acc, m) => {
    acc[m.status] = (acc[m.status] ?? 0) + 1;
    return acc;
  }, {});

  const filterOptions = ['All', 'Critical', 'Warning', 'Scheduled', 'Normal'];

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="bg-white p-6 rounded-2xl border border-slate-100 animate-pulse">
            <div className="h-8 bg-slate-100 rounded mb-4 w-1/2" />
            <div className="h-4 bg-slate-100 rounded mb-2 w-3/4" />
            <div className="h-4 bg-slate-100 rounded w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div>
      {/* Filter pills + count */}
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div className="flex gap-2 flex-wrap">
          {filterOptions.map((f) => {
            const count = f === 'All' ? allMachines.length : (counts[f] ?? 0);
            const isActive = statusFilter === f;
            return (
              <button
                key={f}
                onClick={() => setStatusFilter(f)}
                className={`px-3 py-1.5 rounded-full text-xs font-bold border transition-all ${
                  isActive
                    ? 'bg-primary text-white border-primary'
                    : 'bg-white text-slate-500 border-slate-200 hover:border-primary hover:text-primary'
                }`}
              >
                {f}
                {count > 0 && (
                  <span className={`ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] ${
                    isActive ? 'bg-white/20' : 'bg-slate-100'
                  }`}>
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
        <span className="text-xs text-slate-400">
          Showing {paginated.length} of {filtered.length} machines
        </span>
      </div>

      {/* Machine cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {paginated.map((machine) => {
          const config = statusConfig[machine.status] ?? statusConfig.Normal;
          return (
            <div
              key={machine.machine_id}
              className="bg-white p-6 rounded-2xl border border-slate-100 shadow-[0_2px_12px_rgba(15,23,42,0.03)] hover:shadow-[0_4px_20px_rgba(15,23,42,0.06)] transition-all duration-200"
            >
              <div className="flex justify-between items-center mb-5">
                <div className={`p-2 rounded-xl ${config.iconBg}`}>
                  <span className="material-icons-round text-xl block">{config.icon}</span>
                </div>
                <span className={`${config.badge} text-[10px] font-bold px-2.5 py-1 rounded-lg uppercase tracking-wider`}>
                  {machine.status}
                </span>
              </div>

              <h4 className="font-bold text-lg text-light tracking-tight mb-0.5">
                {machine.machine_id}
              </h4>
              <p className="text-xs text-muted mb-5">
                RUL: <span className="font-medium text-light">{machine.current_rul_days} days</span>
              </p>

              <div className="space-y-3 pt-3 border-t border-slate-100">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-muted">s₉ Pressure</span>
                  <span className={`font-mono ${config.metricsColor}`}>
                    {machine.avg_vibration} 
                  </span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-muted">s₄ HPC Temp</span>
                  <span className="font-mono font-semibold text-light">
                    {machine.avg_temperature}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-8">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="p-2 rounded-xl border border-slate-200 text-slate-400 hover:text-primary hover:border-primary disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <span className="material-icons-round text-lg">chevron_left</span>
          </button>

          {Array.from({ length: totalPages }).map((_, i) => {
            const pg = i + 1;
            // Show first, last, current ±1, with ellipsis
            if (
              pg === 1 ||
              pg === totalPages ||
              (pg >= page - 1 && pg <= page + 1)
            ) {
              return (
                <button
                  key={pg}
                  onClick={() => setPage(pg)}
                  className={`w-9 h-9 rounded-xl text-sm font-bold transition-colors ${
                    pg === page
                      ? 'bg-primary text-white'
                      : 'border border-slate-200 text-slate-500 hover:border-primary hover:text-primary'
                  }`}
                >
                  {pg}
                </button>
              );
            }
            if (pg === page - 2 || pg === page + 2) {
              return <span key={pg} className="text-slate-300 text-sm">…</span>;
            }
            return null;
          })}

          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="p-2 rounded-xl border border-slate-200 text-slate-400 hover:text-primary hover:border-primary disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <span className="material-icons-round text-lg">chevron_right</span>
          </button>
        </div>
      )}
    </div>
  );
}