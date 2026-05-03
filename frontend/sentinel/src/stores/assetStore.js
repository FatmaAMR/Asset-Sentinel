import { create } from 'zustand';
import {
  getFactorySummary,
  getMachineDetails,
  getMachineHistory,
  getAlerts
} from '../api/assetApi';

const useAssetStore = create((set) => ({
  factorySummary: null,
  machineDetails: null,
  machineHistory: [],
  alerts: [],
  loading: false,
  error: null,

  fetchFactorySummary: async (status = null) => {
    set({ loading: true, error: null });
    try {
      const res = await getFactorySummary(status);
      set({ factorySummary: res.data });
    } catch (err) {
      set({ error: err.message });
    } finally {
      set({ loading: false });
    }
  },

  fetchMachineDetails: async (machineId) => {
    set({ loading: true, error: null });
    try {
      const res = await getMachineDetails(machineId);
      set({ machineDetails: res.data });
    } catch (err) {
      set({ error: err.message });
    } finally {
      set({ loading: false });
    }
  },

  fetchMachineHistory: async (machineId, limit = 50) => {
    set({ loading: true, error: null });
    try {
      const res = await getMachineHistory(machineId, limit);
      set({ machineHistory: res.data });
    } catch (err) {
      set({ error: err.message });
    } finally {
      set({ loading: false });
    }
  },

  fetchAlerts: async (status = null) => {
    set({ loading: true, error: null });
    try {
      const res = await getAlerts(status);
      set({ alerts: res.data });
    } catch (err) {
      set({ error: err.message });
    } finally {
      set({ loading: false });
    }
  },
}));

export default useAssetStore;