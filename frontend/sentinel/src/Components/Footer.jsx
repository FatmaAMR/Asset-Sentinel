export default function Footer() {
  return (
    <footer className="mt-12 py-6 border-t border-gray-200">
      <div className="max-w-[1440px] mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-4 text-slate-500 text-xs">
        <div className="flex items-center gap-6">
          <span className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-normal" />
            API Connected: 12ms
          </span>
          <span className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-normal" />
            Local LLM: Active
          </span>
          <span>Version 2.4.0-build.82</span>
        </div>
        <div className="flex items-center gap-6">
          <a href="#" className="hover:text-primary transition-colors">Documentation</a>
          <a href="#" className="hover:text-primary transition-colors">Support</a>
          <a href="#" className="hover:text-primary transition-colors">Terms of Service</a>
        </div>

      </div>
    </footer>
  );
}