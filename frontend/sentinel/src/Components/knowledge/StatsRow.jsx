export default function StatsRow() {
  return (
    <section className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-8 py-10 border-t border-slate-200 dark:border-slate-800">
      <div>
        <span className="block text-3xl font-display font-extrabold text-primary mb-1">
          42,000+
        </span>
        <span className="text-sm font-bold text-slate-400 uppercase tracking-widest">
          Total Chunks
        </span>
      </div>
      <div>
        <span className="block text-3xl font-display font-extrabold text-primary mb-1">
          156
        </span>
        <span className="text-sm font-bold text-slate-400 uppercase tracking-widest">
          Library Docs
        </span>
      </div>
      <div>
        <span className="block text-3xl font-display font-extrabold text-primary mb-1">
          2.4ms
        </span>
        <span className="text-sm font-bold text-slate-400 uppercase tracking-widest">
          Retrieval Latency
        </span>
      </div>
      <div>
        <span className="block text-3xl font-display font-extrabold text-primary mb-1">
          0.92
        </span>
        <span className="text-sm font-bold text-slate-400 uppercase tracking-widest">
          Avg. Similarity
        </span>
      </div>
    </section>
  );
}
