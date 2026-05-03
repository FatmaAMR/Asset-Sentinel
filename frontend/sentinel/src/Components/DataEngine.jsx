import { useState } from "react";

export default function DataEngine() {
  const [mode, setMode] = useState("simulated");

  return (
    <section className="bg-primary p-8 rounded-3xl text-white relative overflow-hidden group">
      <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <h2 className="text-2xl font-bold mb-2">Data Ingestion Engine</h2>
          <p className="text-white/70">
            Switch between simulation mode for testing and production real-time feeds.
          </p>
        </div>
        <div className="bg-white/20 p-1 rounded-2xl flex items-center">
          <button
            onClick={() => setMode("simulated")}
            className={`px-6 py-2.5 rounded-xl font-bold transition-all ${
              mode === "simulated"
                ? "bg-white text-primary shadow-lg"
                : "text-white/70 hover:text-white"
            }`}
          >
            Simulated
          </button>
          <button
            onClick={() => setMode("realtime")}
            className={`px-6 py-2.5 rounded-xl font-bold transition-all ${
              mode === "realtime"
                ? "bg-white text-primary shadow-lg"
                : "text-white/70 hover:text-white"
            }`}
          >
            Real-time
          </button>
        </div>

      </div>
      <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-white/10 rounded-full blur-3xl group-hover:scale-110 transition-transform" />
      <div className="absolute right-20 -top-10 w-24 h-24 bg-white/5 rounded-full blur-2xl" />

    </section>
  );
}