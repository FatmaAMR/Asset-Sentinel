import { create } from 'zustand';
import axios from 'axios';

const BASE = 'http://localhost:8001/api/v1/managerial';

const useManagerialStore = create((set, get) => ({
  token: localStorage.getItem('sentinel_token') || null,
  assets: [],
  thresholds: [],
  loading: false,
  error: null,

  login: async (username, password) => {
    set({ loading: true, error: null });
    try {
      const form = new URLSearchParams();
      form.append('grant_type', 'password');
      form.append('username', username.trim());
      form.append('password', password.trim());

      const res = await axios.post(`${BASE}/auth/login`, form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      const token = res.data.access_token;
      localStorage.setItem('sentinel_token', token);
      set({ token });
      return true;
    } catch (err) {
      set({ error: 'Invalid credentials' });
      return false;
    } finally {
      set({ loading: false });
    }
  },

  logout: () => {
    localStorage.removeItem('sentinel_token');
    set({ token: null });
  },

  fetchAssets: async () => {
    set({ loading: true });
    try {
      const res = await axios.get(`${BASE}/assets/`, {
        headers: { Authorization: `Bearer ${get().token}` }
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
        headers: { Authorization: `Bearer ${get().token}` }
      });
      get().fetchAssets();
    } catch (err) {
      set({ error: err.message });
    }
  },

  deleteAsset: async (assetId) => {
    try {
      await axios.delete(`${BASE}/assets/${assetId}`, {
        headers: { Authorization: `Bearer ${get().token}` }
      });
      get().fetchAssets();
    } catch (err) {
      set({ error: err.message });
    }
  },


  fetchThresholds: async () => {
    set({ loading: true });
    try {
      const res = await axios.get(`${BASE}/thresholds/`, {
        headers: { Authorization: `Bearer ${get().token}` }
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
      await axios.post(`${BASE}/thresholds/`, rule, {
        headers: { Authorization: `Bearer ${get().token}` }
      });
      get().fetchThresholds();
    } catch (err) {
      set({ error: err.message });
    }
  },

  deleteThreshold: async (ruleId) => {
    try {
      await axios.delete(`${BASE}/thresholds/${ruleId}`, {
        headers: { Authorization: `Bearer ${get().token}` }
      });
      get().fetchThresholds();
    } catch (err) {
      set({ error: err.message });
    }
  },
}));

export default useManagerialStore;