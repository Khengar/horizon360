import axios from 'axios';

const BASE_URL = `http://${window.location.hostname}:8000/api`;

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to inject JWT token and company API key
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('jwt_token');
  const apiToken = localStorage.getItem('company_api_token');
  if (config.headers) {
    if (token) {
      if (typeof (config.headers as any).set === 'function') {
        (config.headers as any).set('Authorization', `Bearer ${token}`);
      } else {
        (config.headers as any)['Authorization'] = `Bearer ${token}`;
      }
    }
    if (apiToken) {
      if (typeof (config.headers as any).set === 'function') {
        (config.headers as any).set('X-API-Key', apiToken);
      } else {
        (config.headers as any)['X-API-Key'] = apiToken;
      }
    }
  }
  return config;
});

// Interceptor to automatically logout on 401 or 403 authentication expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const isAuthError =
        error.response.status === 401 ||
        (error.response.status === 403 &&
          (error.response.data?.code === 'not_authenticated' ||
           error.response.data?.code === 'token_not_valid' ||
           (typeof error.response.data?.detail === 'string' &&
             (error.response.data.detail.toLowerCase().includes('credential') ||
              error.response.data.detail.toLowerCase().includes('token')))));

      if (isAuthError && !window.location.pathname.startsWith('/login')) {
        localStorage.removeItem('jwt_token');
        localStorage.removeItem('company_api_token');
        window.location.href = '/login';
      }
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
  createCustomer: async (data: any) => {
    const res = await api.post('/customers/', data);
    return res.data;
  },
  updateCustomer: async (id: string, data: any) => {
    const res = await api.patch(`/customers/${id}/`, data);
    return res.data;
  },
  deleteCustomer: async (id: string) => {
    const res = await api.delete(`/customers/${id}/`);
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

  deleteDeal: async (id: number | string) => {
    const res = await api.delete(`/crm/deals/${id}/`);
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
  getCampaigns: async (page?: number) => {
    const url = page !== undefined ? `/marketing/campaigns/?page=${page}` : '/marketing/campaigns/';
    const res = await api.get(url);
    return res.data;
  },
  getCampaign: async (id: number | string) => {
    const res = await api.get(`/marketing/campaigns/${id}/`);
    return res.data;
  },
  updateCampaign: async (id: number | string, data: any) => {
    const res = await api.patch(`/marketing/campaigns/${id}/`, data);
    return res.data;
  },
  deleteCampaign: async (id: number | string) => {
    const res = await api.delete(`/marketing/campaigns/${id}/`);
    return res.data;
  },
  previewCampaignAudience: async (id: number | string) => {
    const res = await api.post(`/marketing/campaigns/${id}/preview-audience/`);
    return res.data;
  },
  sendCampaignNow: async (id: number | string) => {
    const res = await api.post(`/marketing/campaigns/${id}/send-now/`);
    return res.data;
  },
  scheduleCampaign: async (id: number | string, data: any) => {
    const res = await api.post(`/marketing/campaigns/${id}/schedule/`, data);
    return res.data;
  },
  pauseCampaign: async (id: number | string) => {
    const res = await api.post(`/marketing/campaigns/${id}/pause/`);
    return res.data;
  },
  resumeCampaign: async (id: number | string) => {
    const res = await api.post(`/marketing/campaigns/${id}/resume/`);
    return res.data;
  },
  duplicateCampaign: async (id: number | string) => {
    const res = await api.post(`/marketing/campaigns/${id}/duplicate/`);
    return res.data;
  },
  getCampaignAnalytics: async (id: number | string) => {
    const res = await api.get(`/marketing/campaigns/${id}/analytics/`);
    return res.data;
  },
  generateCampaignAudience: async (id: number | string, data: any = {}) => {
    const res = await api.post(`/marketing/campaigns/${id}/generate-audience/`, data);
    return res.data;
  },
  generateCampaignCopy: async (id: number | string, data: any) => {
    const res = await api.post(`/marketing/campaigns/${id}/generate-copy/`, data);
    return res.data;
  },
  getCampaignAttributionBriefing: async (id: number | string) => {
    const res = await api.get(`/marketing/campaigns/${id}/attribution-briefing/`);
    return res.data;
  },
  getCampaignContents: async (campaignId: number | string) => {
    const res = await api.get(`/marketing/contents/?campaign=${campaignId}`);
    return res.data;
  },
  createCampaignContent: async (data: any) => {
    const res = await api.post('/marketing/contents/', data);
    return res.data;
  },
  updateCampaignContent: async (id: number | string, data: any) => {
    const res = await api.patch(`/marketing/contents/${id}/`, data);
    return res.data;
  },
  deleteCampaignContent: async (id: number | string) => {
    const res = await api.delete(`/marketing/contents/${id}/`);
    return res.data;
  },
  previewCampaignContent: async (contentId: number | string, customerId?: string) => {
    const res = await api.post(`/marketing/contents/${contentId}/preview/`, { customer_id: customerId });
    return res.data;
  },
  getCampaignRecipients: async (campaignId: number | string, page = 1) => {
    const res = await api.get(`/marketing/recipients/?campaign=${campaignId}&page=${page}`);
    return res.data;
  },
  getCampaignEvents: async (campaignId: number | string, page = 1) => {
    const res = await api.get(`/marketing/events/?campaign=${campaignId}&page=${page}`);
    return res.data;
  },
  getMarketingTemplates: async () => {
    const res = await api.get('/marketing/templates/');
    return res.data;
  },
  createMarketingTemplate: async (data: any) => {
    const res = await api.post('/marketing/templates/', data);
    return res.data;
  },
  getMarketingDashboard: async () => {
    const res = await api.get('/marketing/dashboard/');
    return res.data;
  },
  getAllSegments: async () => {
    const res = await api.get('/segments/');
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
  updateEmployee: async (id: number | string, data: any) => {
    const res = await api.patch(`/hrms/employees/${id}/`, data);
    return res.data;
  },
  deleteEmployee: async (id: number | string) => {
    const res = await api.delete(`/hrms/employees/${id}/`);
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
  createProduct: async (data: any) => {
    const res = await api.post('/finance/products/', data);
    return res.data;
  },
  updateProduct: async (id: number | string, data: any) => {
    const res = await api.patch(`/finance/products/${id}/`, data);
    return res.data;
  },
  deleteProduct: async (id: number | string) => {
    const res = await api.delete(`/finance/products/${id}/`);
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
  updateWorkflow: async (id: number | string, data: any) => {
    const res = await api.patch(`/workflows/${id}/`, data);
    return res.data;
  },
  createWorkflow: async (data: any) => {
    const res = await api.post('/workflows/', data);
    return res.data;
  },

  // Flow Engine V2
  getV2Flows: async () => {
    const res = await api.get('/v2/flow-engine/flows/');
    return res.data;
  },
  getV2FlowDetail: async (id: string) => {
    const res = await api.get(`/v2/flow-engine/flows/${id}/`);
    return res.data;
  },
  createV2Flow: async (data: any) => {
    const res = await api.post('/v2/flow-engine/flows/', data);
    return res.data;
  },
  getV2FlowVersion: async (versionId: string) => {
    const res = await api.get(`/v2/flow-engine/flow-versions/${versionId}/`);
    return res.data;
  },
  saveV2FlowCanvas: async (versionId: string, nodes: any[], edges: any[]) => {
    const res = await api.put(`/v2/flow-engine/flow-versions/${versionId}/canvas/`, { nodes, edges });
    return res.data;
  },
  updateV2FlowTrigger: async (flowId: string, data: any) => {
    const res = await api.put(`/v2/flow-engine/flows/${flowId}/update_trigger/`, data);
    return res.data;
  },
  getV2FlowAnalytics: async () => {
    const res = await api.get('/v2/flow-engine/flow-analytics/dashboard/');
    return res.data;
  },
  getFlowAuditLogs: async () => {
    const res = await api.get('/v2/flow-engine/flow-audit/');
    return res.data;
  },
  getV2Executions: async () => {
    const res = await api.get('/v2/flow-engine/executions/');
    return res.data;
  },
  getV2Execution: async (id: string) => {
    const res = await api.get(`/v2/flow-engine/executions/${id}/`);
    return res.data;
  },
  getV2Templates: async () => {
    const res = await api.get('/v2/flow-engine/flow-templates/');
    return res.data;
  },
  
  // Flow Engine Approvals
  getV2Approvals: async () => {
    const res = await api.get('/v2/flow-engine/approvals/');
    return res.data;
  },
  approveV2Approval: async (id: string, comment: string = '') => {
    const res = await api.post(`/v2/flow-engine/approvals/${id}/approve/`, { comment });
    return res.data;
  },
  rejectV2Approval: async (id: string, comment: string = '') => {
    const res = await api.post(`/v2/flow-engine/approvals/${id}/reject/`, { comment });
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
  createCompany: async (data: any) => {
    const res = await api.post('/accounts/', data);
    return res.data;
  },
  updateCompany: async (id: string, data: any) => {
    const res = await api.patch(`/accounts/${id}/`, data);
    return res.data;
  },
  deleteCompany: async (id: string) => {
    const res = await api.delete(`/accounts/${id}/`);
    return res.data;
  },

  // SLA Policies
  getSLAPolicies: async (flowId: string) => {
    const res = await api.get(`/v2/flow-engine/sla-policies/?flow=${flowId}`);
    return res.data;
  },
  createSLAPolicy: async (data: any) => {
    const res = await api.post('/v2/flow-engine/sla-policies/', data);
    return res.data;
  },
  deleteSLAPolicy: async (id: string) => {
    const res = await api.delete(`/v2/flow-engine/sla-policies/${id}/`);
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
