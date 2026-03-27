import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// ── Response interceptor — auto-redirect on 401 ───────────────────────────────
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      // Token expired or invalid — clear session and go to login
      sessionStorage.removeItem('token');
      delete api.defaults.headers.common['Authorization'];
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────
export const getCurrentUser = () => api.get('/users/me');
export const getUsers       = () => api.get('/users');
export const registerUser   = (data) => api.post('/register', data);

// ── Departments ───────────────────────────────────────────────────────────────
export const getDepartments   = ()     => api.get('/departments');
export const getDepartment    = (id)   => api.get(`/departments/${id}`);
export const createDepartment = (data) => api.post('/departments', data);

// ── Officers ──────────────────────────────────────────────────────────────────
export const getOfficers   = (p={}) => api.get('/officers', { params: p });
export const getOfficer    = (id)   => api.get(`/officers/${id}`);
export const createOfficer = (data) => api.post('/officers', data);

// ── Incident Types ────────────────────────────────────────────────────────────
export const getIncidentTypes = () => api.get('/incident-types');

// ── Incidents ─────────────────────────────────────────────────────────────────
export const searchIncidents  = (p={})   => api.get('/incidents', { params: p });
export const getIncident      = (id)     => api.get(`/incidents/${id}`);
export const createIncident   = (data)   => api.post('/incidents', data);
export const updateWorkflow   = (id, params) => api.put(`/incidents/${id}/workflow`, null, { params });

// ── Outcomes & Complaints ─────────────────────────────────────────────────────
export const getOutcomes      = (p={})   => api.get('/outcomes',   { params: p });
export const createOutcome    = (data)   => api.post('/outcomes',   data);
export const getComplaints    = (p={})   => api.get('/complaints',  { params: p });
export const createComplaint  = (data)   => api.post('/complaints', data);

// ── Statistics ────────────────────────────────────────────────────────────────
export const getIncidentStats = () => api.get('/stats/incidents');
export const getOfficerStats  = () => api.get('/stats/officers');

export default api;
