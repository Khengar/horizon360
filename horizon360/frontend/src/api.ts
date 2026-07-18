import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to inject JWT token if it exists
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('jwt_token');
  if (token && config.headers) {
    config.headers.set('Authorization', `Bearer ${token}`);
  }
  return config;
});

// Interceptor to automatically logout on 401 expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('jwt_token');
      localStorage.removeItem('company_api_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const horizonApi = {
  // Authentication
  login: async (credentials: any) => {
    const res = await api.post('/auth/login/', credentials);
    if (res.data.access) {
      localStorage.setItem('jwt_token', res.data.access);
      localStorage.setItem('company_api_token', res.data.company_api_token);
    }
    return res.data;
  },
  
  // Customers / CRM
  getCustomers: async (emailQuery?: string) => {
    const params = emailQuery ? { email: emailQuery } : {};
    const res = await api.get('/customers/', { params });
    return res.data;
  },
  
  getCustomerDetail: async (id: string) => {
    const res = await api.get(`/customers/${id}/`);
    return res.data;
  },

  // Dynamic Segments
  getSegment: async (segmentName: string) => {
    const res = await api.get(`/segments/${segmentName}/`);
    return res.data;
  }
};
