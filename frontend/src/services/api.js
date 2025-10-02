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
  googleAuth: (token) => api.post('/auth/google/', { token }),
  logout: () => api.post('/auth/logout/'),
  getProfile: () => api.get('/users/me/'),
  updateProfile: (userData) => api.patch('/users/me/', userData),
  refreshToken: (refresh) => api.post('/auth/refresh/', { refresh }),
  changePassword: (passwordData) => api.post('/auth/change-password/', passwordData),
  deleteAccount: () => api.delete('/users/delete-account/'),
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
  getSettings: () => api.get('/users/settings/'),
  updateSettings: (settings) => api.patch('/users/settings/', settings),
};

// Analytics API
export const analyticsAPI = {
  getDashboard: () => api.get('/analytics/dashboard/'),
  getPerformance: () => api.get('/analytics/performance/'),
  getUserAnalytics: () => api.get('/analytics/user_analytics/'),
  exportData: (format) => api.post('/analytics/export/', { format }),
};

// Security API
export const securityAPI = {
  checkRateLimit: (action) => api.post('/security/check_rate_limit/', { action }),
  validateFile: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/security/validate_file/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  moderateText: (text) => api.post('/security/moderate_text/', { text }),
};

// Mobile API
export const mobileAPI = {
  cameraCapture: (imageData) => api.post('/mobile/camera_capture/', { image_data: imageData }),
  enableOffline: (momentIds) => api.post('/mobile/enable_offline/', { moment_ids: momentIds }),
  syncOffline: (data) => api.post('/mobile/sync_offline/', data),
  registerFCM: (token) => api.post('/mobile/register_fcm/', { token }),
  getCameraConfig: () => api.get('/mobile/camera_config/'),
};

// AI API
export const aiAPI = {
  analyzeImage: (imageData) => {
    const formData = new FormData();
    formData.append('image', imageData);
    return api.post('/ai/analyze_image/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  smartCompress: (imageData, options = {}) => {
    const formData = new FormData();
    formData.append('image', imageData);
    Object.keys(options).forEach(key => {
      formData.append(key, options[key]);
    });
    return api.post('/ai/smart_compress/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  generateTags: (imageData) => {
    const formData = new FormData();
    formData.append('image', imageData);
    return api.post('/ai/generate_tags/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// Storage API
export const storageAPI = {
  uploadMedia: (file, options = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    Object.keys(options).forEach(key => {
      formData.append(key, options[key]);
    });
    return api.post('/storage/upload_media/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getMediaInfo: (fileId) => api.get('/storage/media_info/', { params: { file_id: fileId } }),
  optimizeStorage: () => api.post('/storage/optimize_storage/'),
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

// Comprehensive API service with all endpoints
export const apiService = {
  // Authentication
  auth: authAPI,
  
  // Core functionality
  moments: momentAPI,
  media: mediaAPI,
  users: userAPI,
  
  // Advanced features
  analytics: analyticsAPI,
  security: securityAPI,
  mobile: mobileAPI,
  ai: aiAPI,
  storage: storageAPI,
  websocket: websocketAPI,
  
  // Utility functions
  handleError: handleApiError,
  
  // Direct API access
  get: (url, config) => api.get(url, config),
  post: (url, data, config) => api.post(url, data, config),
  put: (url, data, config) => api.put(url, data, config),
  patch: (url, data, config) => api.patch(url, data, config),
  delete: (url, config) => api.delete(url, config),
};

export default api;
