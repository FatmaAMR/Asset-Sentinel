export default function LeftRail() {
  return (
    <aside className="w-16 border-r border-slate-200 dark:border-slate-800 flex flex-col items-center py-6 gap-6 bg-white dark:bg-card-dark">
      <button className="p-2 rounded-xl bg-primary/10 text-primary">
        <span className="material-symbols-rounded">analytics</span>
      </button>

      <button className="p-2 rounded-xl text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800">
        <span className="material-symbols-rounded">
          settings_input_component
        </span>
      </button>

      <button className="p-2 rounded-xl text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800">
        <span className="material-symbols-rounded">description</span>
      </button>

      <div className="mt-auto">
        <button className="p-2 rounded-xl text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800">
          <span className="material-symbols-rounded">settings</span>
        </button>
      </div>
    </aside>
  );
}
