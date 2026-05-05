import { useEffect, useState } from 'react';
import useManagerialStore from '../stores/managerialStore';

const statusColors = {
  Active: 'bg-normal/10 text-normal',
  Inactive: 'bg-slate-100 text-slate-500',
  Maintenance: 'bg-warning/10 text-warning',
  Critical: 'bg-failure/10 text-failure',
};

export default function Assets() {
  const assets = useManagerialStore((state) => state.assets);
  const loading = useManagerialStore((state) => state.loading);
  const fetchAssets = useManagerialStore((state) => state.fetchAssets);
  const createAsset = useManagerialStore((state) => state.createAsset);
  const deleteAsset = useManagerialStore((state) => state.deleteAsset);

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    asset_id: '', machine_type: '', location_floor: 0,
    location_section: '', specifications: {}, status: 'Active'
  });

  useEffect(() => { fetchAssets(); }, []);

  const handleCreate = async () => {
    await createAsset(form);
    setShowForm(false);
    setForm({ asset_id: '', machine_type: '', location_floor: 0, location_section: '', specifications: {}, status: 'Active' });
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Assets Management</h1>
          <p className="text-slate-400 text-sm mt-1">Manage and monitor all fleet assets</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 bg-primary text-white px-5 py-2.5 rounded-2xl text-sm font-semibold hover:opacity-90 transition-opacity"
        >
          <span className="material-icons-round text-sm">add</span>
          Add Asset
        </button>
      </div>

      {showForm && (
        <div className="bg-cards-light rounded-3xl border border-gray-100 shadow-sm p-6 mb-8">
          <h3 className="font-bold text-slate-700 mb-4">New Asset</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[
              { label: 'Asset ID', key: 'asset_id', placeholder: 'MOTOR-001' },
              { label: 'Machine Type', key: 'machine_type', placeholder: 'FD001' },
              { label: 'Location Floor', key: 'location_floor', placeholder: '0', type: 'number' },
              { label: 'Location Section', key: 'location_section', placeholder: 'Section A' },
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
            <div>
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1 block">Status</label>
              <select
                value={form.status}
                onChange={e => setForm({ ...form, status: e.target.value })}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-primary"
              >
                {['Active', 'Inactive', 'Maintenance', 'Critical'].map(s => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </div>
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
        <p className="text-slate-400">Loading assets...</p>
      ) : (
        <div className="bg-cards-light rounded-3xl border border-gray-100 shadow-sm overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100">
                {['Asset ID', 'Machine Type', 'Floor', 'Section', 'Status', 'Actions'].map(h => (
                  <th key={h} className="text-left text-xs font-bold text-slate-400 uppercase tracking-wider px-6 py-4">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {assets.map((asset, i) => (
                <tr key={asset.asset_id} className={i % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                  <td className="px-6 py-4 text-sm font-bold text-slate-800">{asset.asset_id}</td>
                  <td className="px-6 py-4 text-sm text-slate-600">{asset.machine_type}</td>
                  <td className="px-6 py-4 text-sm text-slate-600">{asset.location_floor}</td>
                  <td className="px-6 py-4 text-sm text-slate-600">{asset.location_section}</td>
                  <td className="px-6 py-4">
                    <span className={`text-[10px] font-bold px-2 py-1 rounded-full uppercase ${statusColors[asset.status] ?? 'bg-slate-100 text-slate-500'}`}>
                      {asset.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => deleteAsset(asset.asset_id)}
                      className="text-failure/60 hover:text-failure transition-colors"
                    >
                      <span className="material-icons-round text-sm">delete</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {assets.length === 0 && (
            <p className="text-center text-slate-400 text-sm py-12">No assets found</p>
          )}
        </div>
      )}
    </div>
  );
}