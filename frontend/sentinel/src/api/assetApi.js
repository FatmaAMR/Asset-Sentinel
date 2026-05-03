import client from './axios';

export const getFactorySummary = (status = null) =>
  client.get('/factory-summary', { params: status ? { status } : {} });

export const getMachineDetails = (machineId) =>
  client.get(`/machines/${machineId}`);

export const getMachineHistory = (machineId, limit = 50) =>
  client.get(`/machines/${machineId}/history`, { params: { limit } });

export const getAlerts = (status = null) =>
  client.get('/alerts', { params: status ? { status } : {} });