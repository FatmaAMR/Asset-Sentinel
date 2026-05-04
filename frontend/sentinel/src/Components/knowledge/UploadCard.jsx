export default function UploadCard() {
  return (
    <section className="bg-primary/5 dark:bg-cards-dark border-2 border-dashed border-primary/30 rounded-[2.5rem] p-10 text-center relative overflow-hidden">
      <div className="absolute top-0 right-0 -mr-12 -mt-12 w-48 h-48 bg-primary/10 rounded-full blur-3xl" />
      <div className="relative z-10">
        <div className="w-16 h-16 bg-primary text-white rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-primary/30">
          <span className="material-symbols-rounded text-3xl">
            cloud_upload
          </span>
        </div>
        <h2 className="text-2xl font-display font-bold mb-2">
          Update Knowledge Hub
        </h2>
        <p className="text-slate-500 dark:text-slate-400 mb-8 max-w-sm mx-auto">
          Drag & drop PDF manuals or ISO standards here to index them for the AI
          model.
        </p>

        <div className="flex justify-center gap-4">
          <button className="bg-slate-900 dark:bg-white dark:text-slate-900 text-white px-8 py-3 rounded-full font-bold flex items-center gap-2 hover:opacity-90 transition-opacity">
            Select Files
            <span className="material-symbols-rounded">arrow_forward</span>
          </button>
        </div>
      </div>
    </section>
  );
}
