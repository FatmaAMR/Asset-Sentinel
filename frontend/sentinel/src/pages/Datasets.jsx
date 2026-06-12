import { useEffect, useRef, useState } from 'react';
import useManagerialStore from '../stores/managerialStore';

export default function Datasets() {
  const datasets      = useManagerialStore((s) => s.datasets);
  const loading       = useManagerialStore((s) => s.loading);
  const error         = useManagerialStore((s) => s.error);
  const fetchDatasets  = useManagerialStore((s) => s.fetchDatasets);
  const uploadDataset  = useManagerialStore((s) => s.uploadDataset);
  const deleteDataset  = useManagerialStore((s) => s.deleteDataset);

  const [file, setFile]       = useState(null);
  const [success, setSuccess] = useState(false);
  const inputRef              = useRef(null);

  useEffect(() => { fetchDatasets(); }, []);

  const handleUpload = async () => {
    if (!file) return;
    setSuccess(false);
    const ok = await uploadDataset(file);
    if (ok) {
      setSuccess(true);
      setFile(null);
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Datasets</h1>
          <p className="text-slate-400 text-sm mt-1">Upload and manage training datasets</p>
        </div>
      </div>

      <div className="bg-cards-light rounded-3xl border border-gray-100 shadow-sm p-6 mb-8">
        <h3 className="font-bold text-slate-700 mb-4">Upload CSV Dataset</h3>
        <div className="flex gap-4 items-end flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1 block">
              CSV File
            </label>
            <input
              ref={inputRef}
              type="file"
              accept=".csv"
              onChange={(e) => { setFile(e.target.files[0]); setSuccess(false); }}
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
          </div>
          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className="bg-primary text-white px-6 py-2.5 rounded-xl text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? 'Uploading...' : 'Upload'}
          </button>
        </div>

        {success && (
          <p className="text-green-500 text-sm mt-3 flex items-center gap-1">
            <span className="material-icons-round text-sm">check_circle</span>
            Dataset uploaded successfully.
          </p>
        )}
        {error && (
          <p className="text-red-500 text-sm mt-3 flex items-center gap-1">
            <span className="material-icons-round text-sm">error</span>
            {error}
          </p>
        )}
      </div>

      <div className="bg-cards-light rounded-3xl border border-gray-100 shadow-sm overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100">
              {['Dataset ID', 'File Name', 'Uploaded By', 'Uploaded At', 'Actions'].map((h) => (
                <th key={h} className="text-left text-xs font-bold text-slate-400 uppercase tracking-wider px-6 py-4">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {datasets.map((d, i) => (
              <tr key={d.dataset_id} className={i % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                <td className="px-6 py-4 text-sm font-bold text-slate-800">{d.dataset_id}</td>
                <td className="px-6 py-4 text-sm text-slate-600">{d.original_name}</td>
                <td className="px-6 py-4 text-sm text-slate-600">{d.uploaded_by}</td>
                <td className="px-6 py-4 text-sm text-slate-600">
                  {new Date(d.uploaded_at).toLocaleString()}
                </td>
                <td className="px-6 py-4">
                  <button
                    onClick={() => deleteDataset(d.dataset_id)}
                    className="text-red-400 hover:text-red-600 transition-colors"
                  >
                    <span className="material-icons-round text-sm">delete</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!loading && datasets.length === 0 && (
          <p className="text-center text-slate-400 text-sm py-12">No datasets uploaded yet</p>
        )}
        {loading && (
          <p className="text-center text-slate-400 text-sm py-12">Loading...</p>
        )}
      </div>
    </div>
  );
}