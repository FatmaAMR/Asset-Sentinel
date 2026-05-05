import { useEffect, useState } from 'react';
import useManagerialStore from '../stores/managerialStore';

export default function Thresholds() {
  const { thresholds, loading, fetchThresholds, createThreshold, deleteThreshold } = useManagerialStore();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    machine_type: '', warning_limit: 0, critical_limit: 0
  });

  useEffect(() => { fetchThresholds(); }, []);

  const handleCreate = async () => {
    await createThreshold(form);
    setShowForm(false);
    setForm({ machine_type: '', warning_limit: 0, critical_limit: 0 });
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Threshold Rules</h1>
          <p className="text-slate-400 text-sm mt-1">Configure warning and critical limits per machine type</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 bg-primary text-white px-5 py-2.5 rounded-2xl text-sm font-semibold hover:opacity-90 transition-opacity"
        >
          <span className="material-icons-round text-sm">add</span>
          Add Rule
        </button>
      </div>
      {showForm && (
        <div className="bg-cards-light rounded-3xl border border-gray-100 shadow-sm p-6 mb-8">
          <h3 className="font-bold text-slate-700 mb-4">New Threshold Rule</h3>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Machine Type', key: 'machine_type', placeholder: 'FD001' },
              { label: 'Warning Limit', key: 'warning_limit', placeholder: '80', type: 'number' },
              { label: 'Critical Limit', key: 'critical_limit', placeholder: '90', type: 'number' },
            ].map(({ label, key, placeholder, type }) => (
              <div key={key}>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1 block">{label}</label>
                <input
                  type={type || 'text'}
                  value={form[key]}
                  onChange={e => setForm({ ...form, [key]: type === 'number' ? +e.target.value : e.target.value })}
                  placeholder={placeholder}
                  className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-primary"
                />
              </div>
            ))}
          </div>
          <div className="flex gap-3 mt-4">
            <button onClick={handleCreate} className="bg-primary text-white px-5 py-2 rounded-xl text-sm font-semibold">
              Create
            </button>
            <button onClick={() => setShowForm(false)} className="bg-slate-100 text-slate-600 px-5 py-2 rounded-xl text-sm font-semibold">
              Cancel
            </button>
          </div>
        </div>
      )}
      {loading ? (
        <p className="text-slate-400">Loading thresholds...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {thresholds.map((rule) => (
            <div key={rule.rule_id} className="bg-cards-light rounded-3xl border border-gray-100 shadow-sm p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="p-3 bg-primary/10 rounded-2xl">
                  <span className="material-icons-round text-primary">tune</span>
                </div>
                <button
                  onClick={() => deleteThreshold(rule.rule_id)}
                  className="text-failure/40 hover:text-failure transition-colors"
                >
                  <span className="material-icons-round text-sm">delete</span>
                </button>
              </div>
              <h4 className="font-bold text-lg text-slate-800">{rule.machine_type}</h4>
              <p className="text-xs text-slate-400 mb-4">Rule ID: {rule.rule_id}</p>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">Warning Limit</span>
                  <span className="text-sm font-bold text-warning bg-warning/10 px-2 py-0.5 rounded-full">
                    {rule.warning_limit}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">Critical Limit</span>
                  <span className="text-sm font-bold text-failure bg-failure/10 px-2 py-0.5 rounded-full">
                    {rule.critical_limit}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">Updated By</span>
                  <span className="text-xs text-slate-500 font-mono">{rule.updated_by_staff_id}</span>
                </div>
              </div>
            </div>
          ))}
          {thresholds.length === 0 && (
            <p className="text-slate-400 text-sm col-span-3 text-center py-12">No threshold rules found</p>
          )}
        </div>
      )}
    </div>
  );
}