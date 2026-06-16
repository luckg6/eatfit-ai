import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (username: string, email: string, password: string) =>
    api.post('/auth/register', { username, email, password }),
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  getMe: () => api.get('/auth/me'),
  logout: () => api.post('/auth/logout'),
};

export const profileAPI = {
  get: () => api.get('/profile'),
  update: (data: any) => api.put('/profile', data),
  init: () => api.post('/profile/init'),
};

export const memoriesAPI = {
  list: (memory_type?: string) =>
    api.get('/memories', { params: { memory_type } }),
  create: (data: any) => api.post('/memories', data),
  update: (id: number, data: any) => api.put(`/memories/${id}`, data),
  delete: (id: number) => api.delete(`/memories/${id}`),
  deleteAll: () => api.delete('/memories'),
};

export const mealsAPI = {
  create: (data: any) => api.post('/meals', data),
  getToday: () => api.get('/meals/today'),
  getRecent: (limit = 10) => api.get('/meals/recent', { params: { limit } }),
  getById: (id: number) => api.get(`/meals/${id}`),
  update: (id: number, data: any) => api.put(`/meals/${id}`, data),
  delete: (id: number) => api.delete(`/meals/${id}`),
  getDailySummary: () => api.get('/meals/summary/daily'),
  getWeeklySummary: () => api.get('/meals/summary/weekly'),
};

export const adviceAPI = {
  // Chat (ReAct SSE)
  sendMessageStream: (data: { message: string; scenario?: string; is_training_day?: boolean; session_id?: number; latitude?: number; longitude?: number }) => {
    const token = localStorage.getItem('token');
    return fetch('/api/advice/send-stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(data),
    });
  },

  // Session lifecycle
  createSession: (data?: { title?: string; scenario?: string; is_training_day?: boolean }) =>
    api.post('/advice/sessions', data || {}),
  getSessions: (limit = 20) => api.get('/advice/sessions', { params: { limit } }),
  getSessionMessages: (sessionId: number) =>
    api.get(`/advice/sessions/${sessionId}/messages`),
  updateMessage: (sessionId: number, messageId: number, data: any) =>
    api.patch(`/advice/sessions/${sessionId}/messages/${messageId}`, data),
  deleteSession: (sessionId: number) =>
    api.delete(`/advice/sessions/${sessionId}`),

  // History (called by Dashboard for "recent advice" widget)
  getHistory: (limit = 20) => api.get('/advice/history', { params: { limit } }),

  // Weekly review (called by WeeklyReview page)
  generateWeeklyReview: () => api.post('/advice/weekly-review'),
};

export const weightsAPI = {
  create: (data: { weight_kg: number; record_date: string; note?: string }) =>
    api.post('/weights', data),
  list: (limit = 30) => api.get('/weights', { params: { limit } }),
  delete: (id: number) => api.delete(`/weights/${id}`),
};

export const bodyFatAPI = {
  create: (data: { body_fat_percent: number; record_date: string; note?: string }) =>
    api.post('/body-fat', data),
  list: (limit = 30) => api.get('/body-fat', { params: { limit } }),
  delete: (id: number) => api.delete(`/body-fat/${id}`),
};

export const trainingsAPI = {
  create: (data: {
    training_type: string;
    duration_minutes?: number;
    intensity?: string;
    record_date: string;
    note?: string;
  }) => api.post('/trainings', data),
  list: (limit = 30) => api.get('/trainings', { params: { limit } }),
  delete: (id: number) => api.delete(`/trainings/${id}`),
};

export const userAPI = {
  updateAutoMemory: (enabled: boolean) =>
    api.patch('/users/auto-memory', null, { params: { auto_memory_enabled: enabled } }),
};

export default api;