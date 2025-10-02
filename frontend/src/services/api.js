import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });
          
          const { access } = response.data;
          localStorage.setItem('token', access);
          
          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/auth/login/', credentials),
  register: (userData) => api.post('/auth/register/', userData),
  logout: () => api.post('/auth/logout/'),
  getProfile: () => api.get('/users/me/'),
  updateProfile: (userData) => api.patch('/users/me/', userData),
  refreshToken: (refresh) => api.post('/auth/refresh/', { refresh }),
};

// Moment API
export const momentAPI = {
  getMoments: () => api.get('/moments/'),
  getMoment: (momentId) => api.get(`/moments/${momentId}/`),
  createMoment: (momentData) => api.post('/moments/', momentData),
  updateMoment: (momentId, momentData) => api.patch(`/moments/${momentId}/`, momentData),
  deleteMoment: (momentId) => api.delete(`/moments/${momentId}/`),
  addMedia: (momentId, mediaFile) => {
    const formData = new FormData();
    formData.append('media', mediaFile);
    return api.post(`/moments/${momentId}/add_media/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  removeMedia: (momentId, mediaId) => api.delete(`/moments/${momentId}/remove_media/`, {
    data: { media_id: mediaId },
  }),
  inviteUser: (momentId, username) => api.post(`/moments/${momentId}/invite_user/`, {
    username,
  }),
  getWebRTCOffer: (momentId) => api.get(`/moments/${momentId}/webrtc_offer/`),
};

// Media API
export const mediaAPI = {
  uploadMedia: (file, momentId = null) => {
    const formData = new FormData();
    formData.append('media', file);
    if (momentId) {
      formData.append('moment_id', momentId);
    }
    return api.post('/media/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getMedia: (mediaId) => api.get(`/media/${mediaId}/`),
  deleteMedia: (mediaId) => api.delete(`/media/${mediaId}/`),
  getMediaList: (params = {}) => api.get('/media/', { params }),
};

// User API
export const userAPI = {
  searchUsers: (query) => api.get('/users/search/', { params: { q: query } }),
  getUser: (userId) => api.get(`/users/${userId}/`),
  updateUser: (userId, userData) => api.patch(`/users/${userId}/`, userData),
};

// WebSocket API
export const websocketAPI = {
  connect: (momentId) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/moments/${momentId}/`;
    return new WebSocket(wsUrl);
  },
};

// Utility functions
export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    const message = error.response.data?.detail || 
                   error.response.data?.message || 
                   'An error occurred';
    return { message, status: error.response.status };
  } else if (error.request) {
    // Request was made but no response received
    return { message: 'Network error. Please check your connection.', status: 0 };
  } else {
    // Something else happened
    return { message: error.message || 'An unexpected error occurred', status: 0 };
  }
};

export default api;
