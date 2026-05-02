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
    <section className="bg-slate-900 rounded-[2.5rem] p-8 text-white relative overflow-hidden mt-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <span className="w-3 h-3 bg-failure rounded-full animate-pulse" />
            Live Vibration Stream
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Real-time spectral analysis for {MACHINE_ID}
          </p>
        </div>
        <span className="bg-slate-800 text-slate-300 text-[10px] px-3 py-1.5 rounded-full border border-slate-700">
          60FPS LOW LATENCY
        </span>
      </div>

      {loading ? (
        <p className="text-slate-400 text-sm">Loading stream data...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          {/* Time Domain — Vibration */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-4">
              Time Domain (Velocity mm/s)
            </p>
            <div className="h-40 flex items-end gap-1">
              {data.map((d, i) => (
                <div
                  key={i}
                  className="flex-1 bg-primary rounded-t-sm transition-all duration-500"
                  style={{ height: `${(d.vibration / maxVibration) * 100}%`, opacity: 0.4 + (d.vibration / maxVibration) * 0.6 }}
                />
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-4">
              FFT Spectrum (Temperature °C)
            </p>
            <div className="h-40 flex items-end gap-1">
              {data.map((d, i) => (
                <div
                  key={i}
                  className="flex-1 bg-warning rounded-t-sm transition-all duration-500"
                  style={{ height: `${(d.temperature / maxTemp) * 100}%`, opacity: 0.4 + (d.temperature / maxTemp) * 0.6 }}
                />
              ))}
            </div>
          </div>
        </div>
      )}






      <div className="mt-8 pt-8 border-t border-slate-800 flex flex-wrap gap-8">
        <div>
          <span className="block text-slate-500 text-[10px] font-bold uppercase mb-1">Crest Factor</span>
          <span className="text-xl font-mono">{crestFactor}</span>
        </div>
        <div>
          <span className="block text-slate-500 text-[10px] font-bold uppercase mb-1">Kurtosis</span>
          <span className="text-xl font-mono">{kurtosis}</span>
        </div>
        <div>
          <span className="block text-slate-500 text-[10px] font-bold uppercase mb-1">Temperature</span>
          <span className="text-xl font-mono text-normal">{latestTemp}°C</span>
        </div>
        <div className="ml-auto flex items-center gap-4">
          <span className="text-xs text-slate-400">AI analysis running on local edge...</span>
          <button className="bg-white text-slate-900 px-6 py-2 rounded-xl text-xs font-bold hover:bg-primary hover:text-white transition-all">
            Capture Snapshot
          </button>
        </div>
      </div>

    </section>
  );
}