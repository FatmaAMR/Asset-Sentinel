import { create } from 'zustand';
import axios from 'axios';

const BASE = 'http://localhost:8006/api/v1/managerial';

const useManagerialStore = create((set, get) => ({
  token: localStorage.getItem('sentinel_token') || null,
  user: JSON.parse(localStorage.getItem('sentinel_user') || 'null'),
  assets: [],
  thresholds: [],
  datasets: [],
  loading: false,
  error: null,

  // ── Auth ──────────────────────────────────────────────────────────────────

  login: async (username, password) => {
    set({ loading: true, error: null });
    try {
      const form = new URLSearchParams();
      form.append('grant_type', 'password');
      form.append('username', username.trim());
      form.append('password', password.trim());

      const res = await axios.post(`${BASE}/auth/login`, form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      const token = res.data.access_token;
      const payload = JSON.parse(atob(token.split('.')[1]));
      const user = { email: payload.sub, role: payload.role };

      localStorage.setItem('sentinel_token', token);
      localStorage.setItem('sentinel_user', JSON.stringify(user));
      set({ token, user });
      return true;
    } catch (err) {
      const msg = err.response?.data?.detail ?? 'Invalid credentials';
      set({ error: msg });
      return false;
    } finally {
      set({ loading: false });
    }
  },

  logout: () => {
    localStorage.removeItem('sentinel_token');
    localStorage.removeItem('sentinel_user');
    set({ token: null, user: null });
  },

  // ── Assets ────────────────────────────────────────────────────────────────

  fetchAssets: async () => {
    set({ loading: true });
    try {
      const res = await axios.get(`${BASE}/assets/`, {
        headers: { Authorization: `Bearer ${get().token}` },
      });
      set({ assets: res.data });
    } catch (err) {
      set({ error: err.message });
    } finally {
      set({ loading: false });
    }
  },

  createAsset: async (asset) => {
    try {
      await axios.post(`${BASE}/assets/`, asset, {
        headers: { Authorization: `Bearer ${get().token}` },
      });
      get().fetchAssets();
    } catch (err) {
      set({ error: err.message });
    }
  },

  deleteAsset: async (assetId) => {
    try {
      await axios.delete(`${BASE}/assets/${assetId}`, {
        headers: { Authorization: `Bearer ${get().token}` },
      });
      get().fetchAssets();
    } catch (err) {
      set({ error: err.message });
    }
  },

  // ── Thresholds ────────────────────────────────────────────────────────────

  fetchThresholds: async () => {
    set({ loading: true });
    try {
      const res = await axios.get(`${BASE}/thresholds/`, {
        headers: { Authorization: `Bearer ${get().token}` },
      });
      set({ thresholds: res.data });
    } catch (err) {
      set({ error: err.message });
    } finally {
      set({ loading: false });
    }
  },

  createThreshold: async (rule) => {
    try {
      await axios.post(
        `${BASE}/thresholds/`,
        {
          ...rule,
          warning_limit: parseFloat(rule.warning_limit),
          critical_limit: parseFloat(rule.critical_limit),
          updated_by_staff_id: 'EMP-001',
        },
        { headers: { Authorization: `Bearer ${get().token}` } }
      );
      get().fetchThresholds();
    } catch (err) {
      set({ error: err.message });
    }
  },

  deleteThreshold: async (ruleId) => {
    try {
      await axios.delete(`${BASE}/thresholds/${ruleId}`, {
        headers: { Authorization: `Bearer ${get().token}` },
      });
      get().fetchThresholds();
    } catch (err) {
      set({ error: err.message });
    }
  },

  // ── Datasets ──────────────────────────────────────────────────────────────

  fetchDatasets: async () => {
    set({ loading: true, error: null });
    try {
      const res = await axios.get(`${BASE}/datasets/`, {
        headers: { Authorization: `Bearer ${get().token}` },
      });
      set({ datasets: res.data });
    } catch (err) {
      set({ error: err.response?.data?.detail ?? err.message });
    } finally {
      set({ loading: false });
    }
  },
  deleteDataset: async (datasetId) => {
  try {
    await axios.delete(`${BASE}/datasets/${datasetId}`, {
      headers: { Authorization: `Bearer ${get().token}` },
    });
    await get().fetchDatasets();
  } catch (err) {
    set({ error: err.response?.data?.detail ?? err.message });
  }
}
,
  uploadDataset: async (file) => {
    set({ loading: true, error: null });
    try {
      const formData = new FormData();
      formData.append('file', file);
      await axios.post(`${BASE}/datasets/upload`, formData, {
        headers: {
          Authorization: `Bearer ${get().token}`,
          'Content-Type': 'multipart/form-data',
        },
      });
      await get().fetchDatasets();
      return true;
    } catch (err) {
      set({ error: err.response?.data?.detail ?? err.message });
      return false;
    } finally {
      set({ loading: false });
    }
  },
}));

export default useManagerialStore;