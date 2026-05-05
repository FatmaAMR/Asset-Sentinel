import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useManagerialStore from '../stores/managerialStore';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const loading = useManagerialStore((state) => state.loading);
  const error = useManagerialStore((state) => state.error);
  const login = useManagerialStore((state) => state.login);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await login(email, password);
    if (success) navigate('/');
  };

  return (
    <div className="min-h-screen bg-light flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="flex items-center gap-3 mb-10 justify-center">
          <div className="w-10 h-10 bg-primary rounded-2xl flex items-center justify-center shadow-lg">
            <span className="material-icons-round text-white text-xl">shield</span>
          </div>
          <span className="text-slate-800 text-2xl font-bold tracking-tight">SENTINEL</span>
        </div>
        <div className="bg-white rounded-3xl p-8 border border-gray-100 shadow-xl">
          <h2 className="text-slate-800 text-2xl font-bold mb-1">Welcome back</h2>
          <p className="text-slate-400 text-sm mb-8">Sign in to your account to continue</p>

          {error && (
            <div className="mb-6 p-3 bg-failure/10 border border-failure/20 rounded-xl text-failure text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-2 block">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="admin@sentinel.com"
                className="w-full bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3 text-slate-800 placeholder-slate-400 text-sm focus:outline-none focus:border-primary transition-colors"
              />
            </div>
            <div>
              <label className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-2 block">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3 text-slate-800 placeholder-slate-400 text-sm focus:outline-none focus:border-primary transition-colors"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary text-white py-3 rounded-2xl font-semibold text-sm hover:opacity-90 transition-opacity disabled:opacity-50 mt-2 shadow-md"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-slate-400 mt-6">
          Sentinel AI — Industrial Asset Monitoring Platform
        </p>
      </div>
    </div>
  );
}