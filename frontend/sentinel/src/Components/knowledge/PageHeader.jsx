export default function PageHeader() {
  return (
    <header className="mb-12">
      <h1 className="text-4xl md:text-5xl font-display font-extrabold mb-4">
        Predictive <span className="text-primary italic">RAG Library</span>
      </h1>
      <p className="text-slate-500 dark:text-slate-400 text-lg max-w-2xl">
        Manage your technical manuals, ISO standards, and bearing data.
        Sentinel&apos;s local LLMs use this context for fleet-wide diagnostics.
      </p>
    </header>
  );
}
