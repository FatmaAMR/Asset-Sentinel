export default function CTASection() {
  return (
    <section className="mt-12 bg-accent text-slate-900 rounded-[3rem] p-12 relative overflow-hidden">
      <div className="absolute -left-12 -bottom-12 w-64 h-64 bg-white/30 rounded-full blur-3xl" />
      <div className="absolute right-0 top-0 w-32 h-full bg-primary/10 flex flex-col justify-around px-4">
        <div className="w-8 h-8 rounded-full bg-primary/20" />
        <div className="w-12 h-12 rounded-lg bg-primary/20" />
        <div className="w-10 h-10 rounded-full bg-primary/20" />
      </div>

      <div className="relative z-10 max-w-xl">
        <h2 className="text-4xl font-display font-extrabold mb-6 leading-tight">
          Ready to refine your fleet diagnostics?
        </h2>

        <button className="bg-slate-900 text-white px-10 py-4 rounded-full font-bold flex items-center gap-3 group hover:pr-12 transition-all">
          Initialize Indexing
          <span className="material-symbols-rounded group-hover:translate-x-1 transition-transform">
            arrow_right_alt
          </span>
        </button>
      </div>
    </section>
  );
}
