import { useRef } from "react";
import useQueryingStore from "../../stores/queringStore";

export default function UploadCard() {
  const { ingest, loading, ingestResult, error, resetIngest } =
    useQueryingStore();
  const fileRef = useRef(null);

  const handleFile = async (file) => {
    if (!file || !file.name.endsWith(".pdf")) return;
    await ingest(file);
    if (fileRef.current) fileRef.current.value = "";
  };

  const onFileChange = (e) => handleFile(e.target.files?.[0]);

  const onDrop = (e) => {
    e.preventDefault();
    handleFile(e.dataTransfer.files?.[0]);
  };

  return (
    <section
      className="bg-primary/5 dark:bg-cards-dark border-2 border-dashed border-primary/30 rounded-[2.5rem] p-10 text-center relative overflow-hidden"
      onDragOver={(e) => e.preventDefault()}
      onDrop={onDrop}
    >
      <div className="absolute top-0 right-0 -mr-12 -mt-12 w-48 h-48 bg-primary/10 rounded-full blur-3xl" />

      <div className="relative z-10">
        <div className="w-16 h-16 bg-primary text-white rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-primary/30">
          <span className="material-symbols-rounded text-3xl">
            {loading ? "hourglass_top" : "cloud_upload"}
          </span>
        </div>

        <h2 className="text-2xl font-display font-bold mb-2">
          Update Knowledge Hub
        </h2>
        <p className="text-slate-500 dark:text-slate-400 mb-8 max-w-sm mx-auto">
          Drag & drop PDF manuals or ISO standards here to index them for the AI
          model.
        </p>

        {/* Success banner */}
        {ingestResult && (
          <div className="mb-6 flex items-center justify-center gap-3 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 rounded-2xl px-6 py-3 text-sm font-semibold">
            <span className="material-symbols-rounded text-base">
              check_circle
            </span>
            {ingestResult.chunks_added} chunks added —{" "}
            {ingestResult.total_chunks} total in knowledge base
            <button
              onClick={resetIngest}
              className="ml-2 opacity-60 hover:opacity-100"
            >
              <span className="material-symbols-rounded text-base">close</span>
            </button>
          </div>
        )}

        {/* Error banner */}
        {error && (
          <div className="mb-6 flex items-center justify-center gap-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800 rounded-2xl px-6 py-3 text-sm font-semibold">
            <span className="material-symbols-rounded text-base">error</span>
            {error}
            <button
              onClick={resetIngest}
              className="ml-2 opacity-60 hover:opacity-100"
            >
              <span className="material-symbols-rounded text-base">close</span>
            </button>
          </div>
        )}

        <div className="flex justify-center gap-4">
          <input
            ref={fileRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={onFileChange}
            disabled={loading}
          />
          <button
            onClick={() => fileRef.current?.click()}
            disabled={loading}
            className="bg-slate-900 dark:bg-white dark:text-slate-900 text-white px-8 py-3 rounded-full font-bold flex items-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Uploading…" : "Select Files"}
            <span className="material-symbols-rounded">
              {loading ? "sync" : "arrow_forward"}
            </span>
          </button>
        </div>
      </div>
    </section>
  );
}
