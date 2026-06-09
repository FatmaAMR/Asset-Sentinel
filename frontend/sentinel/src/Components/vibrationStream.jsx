import { useEffect } from 'react';
import useAssetStore from '../stores/assetStore';

const MACHINE_ID = 'Machine_1'; 

function calcCrestFactor(data) {
  if (!data.length) return '—';
  const peak = Math.max(...data.map(d => d.vibration));
  const rms = Math.sqrt(data.reduce((sum, d) => sum + d.vibration ** 2, 0) / data.length);
  return rms ? (peak / rms).toFixed(2) : '—';
}

function calcKurtosis(data) {
  if (!data.length) return '—';
  const mean = data.reduce((sum, d) => sum + d.vibration, 0) / data.length;
  const std = Math.sqrt(data.reduce((sum, d) => sum + (d.vibration - mean) ** 2, 0) / data.length);
  if (!std) return '—';
  const kurt = data.reduce((sum, d) => sum + ((d.vibration - mean) / std) ** 4, 0) / data.length;
  return kurt.toFixed(2);
}

export default function VibrationStream() {
  const { machineHistory, loading, fetchMachineHistory } = useAssetStore();

  useEffect(() => {
    fetchMachineHistory(MACHINE_ID, 15);
  }, []);

  const data = machineHistory?.data ?? [];

  const maxVibration = Math.max(...data.map(d => d.vibration), 1);
  const maxTemp = Math.max(...data.map(d => d.temperature), 1);

  const latestTemp = data[data.length - 1]?.temperature ?? '—';
  const crestFactor = calcCrestFactor(data);
  const kurtosis = calcKurtosis(data);

  return (
    // Changed bg-slate-900 to white, changed text-white to text-light, and softened the rounded corners to match standard cards
    <section className="bg-white rounded-2xl p-6 text-light border border-slate-100 shadow-[0_2px_12px_rgba(15,23,42,0.03)] mt-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2 tracking-tight text-light">
            <span className="w-2.5 h-2.5 bg-failure rounded-full animate-pulse" />
            Live Vibration Stream
          </h2>
          <p className="text-muted text-xs mt-0.5">
            Real-time spectral analysis for {MACHINE_ID}
          </p>
        </div>
        {/* Adjusted the pill badge for a cleaner light-mode look */}
        <span className="bg-slate-50 text-muted text-[10px] font-semibold px-3 py-1 rounded-lg border border-slate-200/60 uppercase tracking-wider">
          60FPS LOW LATENCY
        </span>
      </div>

      {loading ? (
        <p className="text-muted text-sm">Loading stream data...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          {/* Time Domain — Vibration */}
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-muted mb-4">
              Time Domain (Velocity mm/s)
            </p>
            {/* Added a subtle light background to chart channels for a cleaner blueprint look */}
            <div className="h-40 flex items-end gap-1 bg-slate-50/50 p-2 rounded-xl border border-slate-100">
              {data.map((d, i) => (
                <div
                  key={i}
                  className="flex-1 bg-primary rounded-t-[2px] transition-all duration-500"
                  style={{ height: `${(d.vibration / maxVibration) * 100}%`, opacity: 0.6 + (d.vibration / maxVibration) * 0.4 }}
                />
              ))}
            </div>
          </div>
          
          {/* FFT Spectrum */}
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-muted mb-4">
              FFT Spectrum (Temperature °C)
            </p>
            <div className="h-40 flex items-end gap-1 bg-slate-50/50 p-2 rounded-xl border border-slate-100">
              {data.map((d, i) => (
                <div
                  key={i}
                  className="flex-1 bg-warning rounded-t-[2px] transition-all duration-500"
                  style={{ height: `${(d.temperature / maxTemp) * 100}%`, opacity: 0.6 + (d.temperature / maxTemp) * 0.4 }}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Footer Data Metrics */}
      <div className="mt-8 pt-6 border-t border-slate-100 flex flex-wrap items-center gap-8">
        <div>
          <span className="block text-muted text-[10px] font-bold uppercase mb-0.5 tracking-wider">Crest Factor</span>
          <span className="text-lg font-mono font-bold text-light">{crestFactor}</span>
        </div>
        <div>
          <span className="block text-muted text-[10px] font-bold uppercase mb-0.5 tracking-wider">Kurtosis</span>
          <span className="text-lg font-mono font-bold text-light">{kurtosis}</span>
        </div>
        <div>
          <span className="block text-muted text-[10px] font-bold uppercase mb-0.5 tracking-wider">Temperature</span>
          <span className="text-lg font-mono font-bold text-normal">{latestTemp}°C</span>
        </div>
        
        {/* Action Button Segment */}
        <div className="ml-auto flex items-center gap-4">
          <span className="text-xs text-muted font-medium hidden sm:inline">AI analysis running on local edge...</span>
          <button className="bg-primary text-white px-5 py-2 rounded-xl text-xs font-bold hover:bg-primary/90 hover:shadow-md active:scale-95 transition-all">
            Capture Snapshot
          </button>
        </div>
      </div>
    </section>
  );
}