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

// Builds API (LibreLane flow management)
export const buildsAPI = {
  getPresets: () =>
    api.get('/api/v1/builds/presets'),

  getPDKs: () =>
    api.get('/api/v1/builds/pdks'),

  getConfig: (projectId: number) =>
    api.get(`/api/v1/builds/${projectId}/build/config`),

  saveConfig: (projectId: number, config: any) =>
    api.put(`/api/v1/builds/${projectId}/build/config`, config),

  startBuild: (projectId: number, data: { config: any }) =>
    api.post(`/api/v1/builds/${projectId}/build`, data),

  getStatus: (projectId: number) =>
    api.get(`/api/v1/builds/${projectId}/build/status`),
};

// Modules API
export const modulesAPI = {
  // List modules in a project
  listModules: (projectId: number, params?: { module_type?: string; search?: string }) =>
    api.get(`/api/v1/projects/${projectId}/modules`, { params }),

  // Get module details
  getModule: (projectId: number, moduleId: number) =>
    api.get(`/api/v1/projects/${projectId}/modules/${moduleId}`),

  // Update module
  updateModule: (projectId: number, moduleId: number, data: { name?: string; description?: string; metadata?: any }) =>
    api.put(`/api/v1/projects/${projectId}/modules/${moduleId}`, data),

  // Delete module
  deleteModule: (projectId: number, moduleId: number) =>
    api.delete(`/api/v1/projects/${projectId}/modules/${moduleId}`),

  // Re-parse all files in project
  reparseProject: (projectId: number) =>
    api.post(`/api/v1/projects/${projectId}/modules/reparse`),

  // Parse specific file
  parseFile: (projectId: number, fileId: number) =>
    api.post(`/api/v1/projects/${projectId}/files/${fileId}/parse`),
};

// Forum API
export const forumAPI = {
  // Categories
  listCategories: () =>
    api.get('/api/v1/forum/categories'),

  // Topics
  createTopic: (data: { title: string; category_id: number; content: string }) =>
    api.post('/api/v1/forum/topics', data),

  listTopics: (categoryId: number, params?: { skip?: number; limit?: number }) =>
    api.get(`/api/v1/forum/categories/${categoryId}/topics`, { params }),

  getTopic: (topicId: number) =>
    api.get(`/api/v1/forum/topics/${topicId}`),

  updateTopic: (topicId: number, data: { title?: string; is_pinned?: boolean; is_locked?: boolean }) =>
    api.put(`/api/v1/forum/topics/${topicId}`, data),

  deleteTopic: (topicId: number) =>
    api.delete(`/api/v1/forum/topics/${topicId}`),

  // Posts
  listPosts: (topicId: number, params?: { skip?: number; limit?: number }) =>
    api.get(`/api/v1/forum/topics/${topicId}/posts`, { params }),

  createPost: (topicId: number, data: { content: string }) =>
    api.post(`/api/v1/forum/topics/${topicId}/posts`, data),

  updatePost: (postId: number, data: { content: string }) =>
    api.put(`/api/v1/forum/posts/${postId}`, data),

  deletePost: (postId: number) =>
    api.delete(`/api/v1/forum/posts/${postId}`),
};
