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

  // Observability & Multi-Agent Intelligence
  getEvents: async () => {
    const res = await api.get('/events-history/');
    return res.data;
  },
  getWorkflows: async () => {
    const res = await api.get('/workflows/');
    return res.data;
  },
  getWorkflowTemplates: async () => {
    const res = await api.get('/workflows/templates/');
    return res.data;
  },
  getWorkflowExecutions: async () => {
    const res = await api.get('/workflow-executions/');
    return res.data;
  },
  getInsights: async (filters?: { agent_type?: string; severity?: string }) => {
    const res = await api.get('/intelligence/insights/', { params: filters });
    return res.data;
  },
  runIntelligenceMesh: async () => {
    const res = await api.post('/intelligence/run/', {});
    return res.data;
  },
  executeAction: async (actionData: {
    action_type: string;
    entity_type?: string;
    entity_id?: string;
    insight_id?: number | string;
    payload?: Record<string, any>;
  }) => {
    const res = await api.post('/intelligence/action/', actionData);
    return res.data;
  },
  askCopilot: async (query: string) => {
    const res = await api.post('/copilot/chat/', { query });
    return res.data;
  },
  getInvoices: async () => {
    const res = await api.get('/finance/invoices/');
    return res.data;
  },
  getTransactions: async (page = 1) => {
    const res = await api.get(`/finance/transactions/?page=${page}`);
    return res.data;
  },
  getExpenses: async () => {
    const res = await api.get('/finance/expenses/');
    return res.data;
  },
  createExpense: async (data: any) => {
    const res = await api.post('/finance/expenses/', data);
    return res.data;
  },
  getServiceEntitlements: async () => {
    const res = await api.get('/service/entitlements/');
    return res.data;
  },
  getServiceTickets: async () => {
    const res = await api.get('/service/tickets/');
    return res.data;
  },
  getCampaignTransactions: async (page = 1) => {
    const res = await api.get(`/marketing/transactions/?page=${page}`);
    return res.data;
  },
  createCampaignTransaction: async (data: any) => {
    const res = await api.post('/marketing/transactions/', data);
    return res.data;
  },
  createCampaign: async (data: any) => {
    const res = await api.post('/marketing/campaigns/', data);
    return res.data;
  },
  getCampaigns: async () => {
    const res = await api.get('/marketing/campaigns/');
    return res.data;
  },
  getLeads: async () => {
    const res = await api.get('/marketing/leads/');
    return res.data;
  },
  getTargets: async (page = 1) => {
    const res = await api.get(`/projects/targets/?page=${page}`);
    return res.data;
  },
  createTarget: async (data: any) => {
    const res = await api.post('/projects/targets/', data);
    return res.data;
  },
  getProjects: async () => {
    const res = await api.get('/projects/projects/');
    return res.data;
  },
  createEmployee: async (data: any) => { const res = await api.post('/hrms/employees/', data); return res.data; },
  getEmployees: async () => {
    const res = await api.get('/hrms/employees/');
    return res.data;
  },
  createLeaveRequest: async (data: any) => { const res = await api.post('/hrms/leave-requests/', data); return res.data; },
  getLeaveRequests: async () => {
    const res = await api.get('/hrms/leave-requests/');
    return res.data;
  },
  createDepartment: async (data: any) => { const res = await api.post('/hrms/departments/', data); return res.data; },
  getDepartments: async () => {
    const res = await api.get('/hrms/departments/');
    return res.data;
  },
  getProducts: async () => {
    const res = await api.get('/finance/products/');
    return res.data;
  },
  createPartner: async (data: any) => { const res = await api.post('/partner/partners/', data); return res.data; },
  getPartners: async () => {
    const res = await api.get('/partner/partners/');
    return res.data;
  },
  createPartnerOpportunity: async (data: any) => { const res = await api.post('/partner/opportunities/', data); return res.data; },
  getPartnerOpportunities: async () => {
    const res = await api.get('/partner/opportunities/');
    return res.data;
  },
  createVendor: async (data: any) => { const res = await api.post('/vendor/vendors/', data); return res.data; },
  getVendors: async () => {
    const res = await api.get('/vendor/vendors/');
    return res.data;
  },
  createPurchaseOrder: async (data: any) => { const res = await api.post('/vendor/purchase-orders/', data); return res.data; },
  getPurchaseOrders: async () => {
    const res = await api.get('/vendor/purchase-orders/');
    return res.data;
  },

  getIntegrations: async () => {
    const res = await api.get('/nexus/integrations/');
    return res.data;
  },
  getIntegrationLogs: async () => {
    const res = await api.get('/nexus/integration-logs/');
    return res.data;
  },
  updateWorkflow: async (id: number, data: any) => {
    const res = await api.patch(`/workflows/${id}/`, data);
    return res.data;
  },
  createWorkflow: async (data: any) => {
    const res = await api.post('/workflows/', data);
    return res.data;
  },

  // CDP 360 Pipeline
  getCDPPipeline: async () => {
    const res = await api.get('/cdp/pipeline/');
    return res.data;
  },
  approveMergeSuggestion: async (id: string) => {
    const res = await api.post(`/cdp/merge-suggestions/${id}/approve/`);
    return res.data;
  },
  rejectMergeSuggestion: async (id: string) => {
    const res = await api.post(`/cdp/merge-suggestions/${id}/reject/`);
    return res.data;
  },
  getCompanies: async () => {
    const res = await api.get('/accounts/');
    return res.data;
  },

  // Business Orchestration
  getOrchestrationStatus: async (dealId?: number | string) => {
    const params = dealId ? { deal_id: dealId } : {};
    const res = await api.get('/crm/orchestration/', { params });
    return res.data;
  },
  triggerOrchestration: async (dealId: number | string) => {
    const res = await api.post('/crm/orchestration/', { deal_id: dealId });
    return res.data;
  },
};
