import axios from 'axios';

const BASE_URL = `http://${window.location.hostname}:8000/api`;

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

  getCustomer360: async (id: string) => {
    const res = await api.get(`/customers/${id}/360/`);
    return res.data;
  },

  // Dynamic Segments
  getSegment: async (segmentName: string) => {
    const res = await api.get(`/segments/${segmentName}/`);
    return res.data;
  },

  // CRM
  getContacts: async () => {
    const res = await api.get('/crm/contacts/');
    return res.data;
  },

  getDeals: async () => {
    const res = await api.get('/crm/deals/');
    return res.data;
  },

  createDeal: async (dealData: any) => {
    const res = await api.post('/crm/deals/', dealData);
    return res.data;
  },

  updateDeal: async (id: number | string, dealData: any) => {
    const res = await api.patch(`/crm/deals/${id}/`, dealData);
    return res.data;
  },

  getDealDetail: async (id: number | string) => {
    const res = await api.get(`/crm/deals/${id}/`);
    return res.data;
  },

  // Observability
  getEvents: async () => {
    const res = await api.get('/events-history/');
    return res.data;
  },
  getWorkflows: async () => {
    const res = await api.get('/workflows/');
    return res.data;
  },
  getWorkflowExecutions: async () => {
    const res = await api.get('/workflow-executions/');
    return res.data;
  },
  getInsights: async () => {
    const res = await api.get('/intelligence/insights/');
    return res.data;
  },
  askCopilot: async (query: string) => {
    const res = await api.post('/copilot/chat/', { query });
    return res.data;
  }
};
