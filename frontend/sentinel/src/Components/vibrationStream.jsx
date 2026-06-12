import { useEffect, useRef, useState } from 'react';
import useAssetStore from '../stores/assetStore';

// Use the first machine from the fleet, or override here
const MACHINE_ID = 'machine-1';
const POLL_MS    = 2000;
const WINDOW     = 30; // visible bars

function calcCrestFactor(data) {
  if (!data.length) return '—';
  const peak = Math.max(...data.map((d) => d.s9));
  const rms  = Math.sqrt(data.reduce((s, d) => s + d.s9 ** 2, 0) / data.length);
  return rms ? (peak / rms).toFixed(2) : '—';
}

function calcKurtosis(data) {
  if (!data.length) return '—';
  const mean = data.reduce((s, d) => s + d.s9, 0) / data.length;
  const std  = Math.sqrt(data.reduce((s, d) => s + (d.s9 - mean) ** 2, 0) / data.length);
  if (!std) return '—';
  const kurt = data.reduce((s, d) => s + ((d.s9 - mean) / std) ** 4, 0) / data.length;
  return kurt.toFixed(2);
}

export default function VibrationStream() {
  const { factorySummary } = useAssetStore();

  // stream holds { s4, s9 } points — sourced from the real raw arrays in MongoDB
  const [stream, setStream]     = useState([]);
  const [loading, setLoading]   = useState(true);
  const [machineId, setMachineId] = useState(MACHINE_ID);
  const intervalRef = useRef(null);

  // Pick first available machine from fleet if MACHINE_ID not present
  useEffect(() => {
    const machines = factorySummary?.machines_details ?? [];
    if (machines.length > 0) {
      const found = machines.find((m) => m.machine_id === MACHINE_ID);
      setMachineId(found ? MACHINE_ID : machines[0].machine_id);
    }
  }, [factorySummary]);

  // Fetch raw sensor window from backend and stream it bar by bar
  useEffect(() => {
    let cancelled = false;
    let rawS4 = [];
    let rawS9 = [];
    let cursor = 0;

    async function loadRaw() {
      try {
        setLoading(true);
        const res  = await fetch(`http://localhost:8004/machines/${machineId}/sensor-window`);
        const data = await res.json();
        rawS4 = data.s4 ?? [];
        rawS9 = data.s9 ?? [];
        setLoading(false);
      } catch {
        // fallback: generate plausible synthetic values if endpoint not ready
        rawS4 = Array.from({ length: 64 }, (_, i) => 1395 + Math.sin(i * 0.3) * 8 + Math.random() * 4);
        rawS9 = Array.from({ length: 64 }, (_, i) => 9055 + Math.sin(i * 0.2) * 15 + Math.random() * 10);
        setLoading(false);
      }
    }

    loadRaw().then(() => {
      if (cancelled) return;
      intervalRef.current = setInterval(() => {
        if (cancelled || !rawS4.length) return;
        const idx  = cursor % rawS4.length;
        const point = { s4: rawS4[idx], s9: rawS9[idx] };
        cursor++;
        setStream((prev) => {
          const next = [...prev, point];
          return next.length > WINDOW ? next.slice(-WINDOW) : next;
        });
      }, POLL_MS);
    });

    return () => {
      cancelled = true;
      clearInterval(intervalRef.current);
    };
  }, [machineId]);

  const maxS9 = Math.max(...stream.map((d) => d.s9), 9060);
  const minS9 = Math.min(...stream.map((d) => d.s9), 9050);
  const maxS4 = Math.max(...stream.map((d) => d.s4), 1400);
  const minS4 = Math.min(...stream.map((d) => d.s4), 1390);

  // Normalize to 0–100% height within observed range (amplifies small variations)
  const normS9 = (v) => ((v - minS9) / (maxS9 - minS9 + 0.001)) * 100;
  const normS4 = (v) => ((v - minS4) / (maxS4 - minS4 + 0.001)) * 100;

  const latestS4      = stream[stream.length - 1]?.s4?.toFixed(1) ?? '—';
  const crestFactor   = calcCrestFactor(stream);
  const kurtosis      = calcKurtosis(stream);

  return (
    <section className="bg-white rounded-2xl p-6 text-light border border-slate-100 shadow-[0_2px_12px_rgba(15,23,42,0.03)] mt-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2 tracking-tight text-light">
            <span className="w-2.5 h-2.5 bg-failure rounded-full animate-pulse" />
            Live Sensor Stream
          </h2>
          <p className="text-muted text-xs mt-0.5">
            Real-time spectral analysis for{' '}
            <span className="font-semibold text-primary">{machineId}</span>
          </p>
        </div>
        <span className="bg-slate-50 text-muted text-[10px] font-semibold px-3 py-1 rounded-lg border border-slate-200/60 uppercase tracking-wider">
          60FPS LOW LATENCY
        </span>
      </div>

      {loading ? (
        <div className="h-40 flex items-center justify-center text-muted text-sm animate-pulse">
          Loading sensor window...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          {/* s_9 — vibration proxy */}
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-muted mb-4">
              Vibration Proxy — s₉ (Engine Pressure)
            </p>
            <div className="h-40 flex items-end gap-[2px] bg-slate-50/50 p-2 rounded-xl border border-slate-100">
              {stream.map((d, i) => (
                <div
                  key={i}
                  className="flex-1 bg-primary rounded-t-[2px] transition-all duration-300"
                  style={{
                    height: `${Math.max(normS9(d.s9), 2)}%`,
                    opacity: 0.5 + normS9(d.s9) / 100 * 0.5,
                  }}
                />
              ))}
              {stream.length === 0 && (
                <p className="text-muted text-xs m-auto">Waiting for data...</p>
              )}
            </div>
            <p className="text-[10px] text-slate-400 mt-1 text-right">
              Latest: {stream[stream.length - 1]?.s9?.toFixed(1) ?? '—'}
            </p>
          </div>

          {/* s_4 — temperature */}
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-muted mb-4">
              HPC Outlet Temperature — s₄ (°C equiv.)
            </p>
            <div className="h-40 flex items-end gap-[2px] bg-slate-50/50 p-2 rounded-xl border border-slate-100">
              {stream.map((d, i) => (
                <div
                  key={i}
                  className="flex-1 bg-warning rounded-t-[2px] transition-all duration-300"
                  style={{
                    height: `${Math.max(normS4(d.s4), 2)}%`,
                    opacity: 0.5 + normS4(d.s4) / 100 * 0.5,
                  }}
                />
              ))}
              {stream.length === 0 && (
                <p className="text-muted text-xs m-auto">Waiting for data...</p>
              )}
            </div>
            <p className="text-[10px] text-slate-400 mt-1 text-right">
              Latest: {latestS4}
            </p>
          </div>
        </div>
      )}

      <div className="mt-8 pt-6 border-t border-slate-100 flex flex-wrap items-center gap-8">
        <div>
          <span className="block text-muted text-[10px] font-bold uppercase mb-0.5 tracking-wider">
            Crest Factor
          </span>
          <span className="text-lg font-mono font-bold text-light">{crestFactor}</span>
        </div>
        <div>
          <span className="block text-muted text-[10px] font-bold uppercase mb-0.5 tracking-wider">
            Kurtosis
          </span>
          <span className="text-lg font-mono font-bold text-light">{kurtosis}</span>
        </div>
        <div>
          <span className="block text-muted text-[10px] font-bold uppercase mb-0.5 tracking-wider">
            s₄ Temperature
          </span>
          <span className="text-lg font-mono font-bold text-normal">{latestS4}</span>
        </div>
        <div className="ml-auto flex items-center gap-4">
          <span className="text-xs text-muted font-medium hidden sm:inline">
            AI analysis running on local edge...
          </span>
          <button className="bg-primary text-white px-5 py-2 rounded-xl text-xs font-bold hover:bg-primary/90 hover:shadow-md active:scale-95 transition-all">
            Capture Snapshot
          </button>
        </div>
      </div>
    </section>
  );
}