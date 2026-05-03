export default function ReportFooter() {
  return (
    <footer className="mt-auto pt-10 border-t border-slate-100 flex justify-between items-end">
      <div className="flex gap-6 items-center">
        <div className="p-2 border border-slate-200 rounded-lg bg-cards-light shadow-sm">
          <div className="w-24 h-24 bg-primary flex items-center justify-center text-white">
            <span className="material-icons-round text-6xl">qr_code_2</span>
          </div>
        </div>
        <div>
          <p className="text-xs font-bold text-slate-400 uppercase mb-1">
            Live Asset Portal
          </p>
          <p className="text-sm text-slate-600 max-w-[200px] leading-tight font-medium">
            Scan to view real-time sensor streams and digital twin model.
          </p>
        </div>
      </div>
      <div className="flex gap-12 text-right">
        <div className="min-w-[180px]">
          <div className="border-b border-slate-300 h-10 mb-2" />
          <p className="text-xs font-bold text-slate-400 uppercase">
            Engineer Signature
          </p>
        </div>
        <div className="min-w-[180px]">
          <div className="border-b border-slate-300 h-10 mb-2 flex items-center justify-center">
            <span className="text-slate-300 italic font-medium">
              Timestamp required
            </span>
          </div>
          <p className="text-xs font-bold text-slate-400 uppercase">
            Approval Date
          </p>
        </div>

      </div>
    </footer>
  );
}