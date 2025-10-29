import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/auth/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    api.post('/api/v1/auth/register', data),
  
  login: (data: { email: string; password: string }) =>
    api.post('/api/v1/auth/login', data),
  
  getCurrentUser: () =>
    api.get('/api/v1/auth/me'),
};

// Projects API
export const projectsAPI = {
  list: (params?: { skip?: number; limit?: number; visibility?: string }) =>
    api.get('/api/v1/projects', { params }),
  
  listPublic: (params?: { skip?: number; limit?: number }) =>
    api.get('/api/v1/projects/public', { params }),
  
  get: (id: number) =>
    api.get(`/api/v1/projects/${id}`),
  
  create: (data: { name: string; description?: string; visibility: string }) =>
    api.post('/api/v1/projects', data),
  
  update: (id: number, data: any) =>
    api.put(`/api/v1/projects/${id}`, data),
  
  delete: (id: number) =>
    api.delete(`/api/v1/projects/${id}`),
};

// Files API
export const filesAPI = {
  list: (projectId: number) =>
    api.get(`/api/v1/projects/${projectId}/files`),
  
  get: (projectId: number, fileId: number) =>
    api.get(`/api/v1/projects/${projectId}/files/${fileId}`),
  
  create: (projectId: number, data: { filename: string; filepath: string; content?: string; mime_type?: string }) =>
    api.post(`/api/v1/projects/${projectId}/files`, data),
  
  update: (projectId: number, fileId: number, data: { content?: string; filename?: string }) =>
    api.put(`/api/v1/projects/${projectId}/files/${fileId}`, data),
  
  delete: (projectId: number, fileId: number) =>
    api.delete(`/api/v1/projects/${projectId}/files/${fileId}`),
};

// Jobs API
export const jobsAPI = {
  list: (projectId: number) =>
    api.get(`/api/v1/projects/${projectId}/jobs`),
  
  get: (projectId: number, jobId: number) =>
    api.get(`/api/v1/projects/${projectId}/jobs/${jobId}`),
  
  create: (projectId: number, data: { job_type: string; config?: any }) =>
    api.post(`/api/v1/projects/${projectId}/jobs`, data),
  
  getLogs: (projectId: number, jobId: number) =>
    api.get(`/api/v1/projects/${projectId}/jobs/${jobId}/logs`),
  
  cancel: (projectId: number, jobId: number) =>
    api.delete(`/api/v1/projects/${projectId}/jobs/${jobId}`),
};
