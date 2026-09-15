import os

CONTENT = """
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Link } from 'react-router-dom';
import { horizonApi } from '../api';
import { Download, Search, Plus, Filter, X, Settings2, Eye, Edit2, Trash2, Building2, User, Briefcase, Package, RefreshCw } from 'lucide-react';

interface CRMEntityConfig {
  title: string;
  fetchFn: () => Promise<any>;
  createFn: (data: any) => Promise<any>;
  updateFn: (id: string | number, data: any) => Promise<any>;
  deleteFn: (id: string | number) => Promise<any>;
  columns: { key: string; label: string; isDefault?: boolean; render?: (val: any, row: any) => React.ReactNode }[];
  fields: { name: string; label: string; type?: string; required?: boolean; options?: {value: string, label: string}[]; source?: string }[];
  filters: { name: string; label: string; options?: {value: string, label: string}[]; source?: string }[];
}

// Hook for clicking outside customize/filter dropdowns
function useOutsideAlerter(ref: React.RefObject<any>, callback: () => void) {
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        callback();
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [ref, callback]);
}

export const CRMCoreListView = ({ entity }: { entity: 'customers' | 'companies' | 'opportunities' | 'employees' | 'products' }) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  
  // Relations
  const [relCompanies, setRelCompanies] = useState<any[]>([]);
  const [relCustomers, setRelCustomers] = useState<any[]>([]);
  const [relEmployees, setRelEmployees] = useState<any[]>([]);

  // Modals
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit' | 'view'>('create');
  const [selectedRecord, setSelectedRecord] = useState<any>(null);
  const [formData, setFormData] = useState<any>({});
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Table State
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  
  // Customization
  const [showCustomize, setShowCustomize] = useState(false);
  const customizeRef = useRef(null);
  useOutsideAlerter(customizeRef, () => setShowCustomize(false));

  // Filters
  const [showFilter, setShowFilter] = useState(false);
  const filterRef = useRef(null);
  useOutsideAlerter(filterRef, () => setShowFilter(false));
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({});

  const loadRelations = async () => {
    try {
      const [comps, custs, emps] = await Promise.all([
        horizonApi.getCompanies(),
        horizonApi.getCustomers(),
        horizonApi.getEmployees()
      ]);
      setRelCompanies(Array.isArray(comps) ? comps : comps.results || []);
      setRelCustomers(Array.isArray(custs) ? custs : custs.results || []);
      setRelEmployees(Array.isArray(emps) ? emps : emps.results || []);
    } catch (e) {
      console.error("Failed to load relations", e);
    }
  };

  useEffect(() => {
    loadRelations();
  }, []);

  const configs: Record<string, CRMEntityConfig> = {
    customers: {
      title: 'Customers',
      fetchFn: () => horizonApi.getCustomers(),
      createFn: (data) => {
        const payload = {
          primary_email: data.primary_email,
          primary_phone: data.primary_phone,
          account: data.company || null,
          attributes: {
            firstName: data.first_name,
            lastName: data.last_name,
            status: data.status
          }
        };
        return horizonApi.createCustomer(payload);
      },
      updateFn: (id, data) => {
        const payload = {
          primary_email: data.primary_email,
          primary_phone: data.primary_phone,
          account: data.company || null,
          attributes: {
            firstName: data.first_name,
            lastName: data.last_name,
            status: data.status
          }
        };
        return horizonApi.updateCustomer(id as string, payload);
      },
      deleteFn: (id) => horizonApi.deleteCustomer(id as string),
      columns: [
        { key: 'first_name', label: 'First Name', isDefault: true, render: (val, row) => val || row.attributes?.firstName || '-' },
        { key: 'last_name', label: 'Last Name', isDefault: true, render: (val, row) => val || row.attributes?.lastName || '-' },
        { key: 'primary_email', label: 'Email', isDefault: true },
        { key: 'primary_phone', label: 'Phone No.', isDefault: true },
        { key: 'account_name', label: 'Company', isDefault: true, render: (val, row) => row.account_name || '-' },
        { key: 'status', label: 'Status', isDefault: true, render: (val, row) => row.attributes?.status || '-' },
        { key: 'created_at', label: 'Created At', render: (val) => val ? new Date(val).toLocaleDateString() : '-' },
        { key: 'updated_at', label: 'Updated At', render: (val) => val ? new Date(val).toLocaleDateString() : '-' }
      ],
      fields: [
        { name: 'first_name', label: 'First Name', required: true },
        { name: 'last_name', label: 'Last Name', required: true },
        { name: 'primary_email', label: 'Email', type: 'email', required: true },
        { name: 'primary_phone', label: 'Phone' },
        { name: 'company', label: 'Company', type: 'select', source: 'companies' },
        { name: 'status', label: 'Status', type: 'select', options: [{value:'Active',label:'Active'},{value:'Inactive',label:'Inactive'}] }
      ],
      filters: [
        { name: 'status', label: 'Status', options: [{value:'Active',label:'Active'},{value:'Inactive',label:'Inactive'}] },
        { name: 'company', label: 'Company', source: 'companies' }
      ]
    },
    companies: {
      title: 'Companies',
      fetchFn: () => horizonApi.getCompanies(),
      createFn: (data) => {
        const payload = {
          name: data.name,
          domain: data.domain,
          industry: data.industry,
          tier: data.tier,
          attributes: {
            phone: data.phone,
            email: data.email,
            address: data.address,
            website: data.website,
            status: data.status
          }
        };
        return horizonApi.createCompany(payload);
      },
      updateFn: (id, data) => {
        const payload = {
          name: data.name,
          domain: data.domain,
          industry: data.industry,
          tier: data.tier,
          attributes: {
            phone: data.phone,
            email: data.email,
            address: data.address,
            website: data.website,
            status: data.status
          }
        };
        return horizonApi.updateCompany(id as string, payload);
      },
      deleteFn: (id) => horizonApi.deleteCompany(id as string),
      columns: [
        { key: 'name', label: 'Company Name', isDefault: true },
        { key: 'domain', label: 'Domain', isDefault: true },
        { key: 'industry', label: 'Industry', isDefault: true },
        { key: 'tier', label: 'Tier', isDefault: true },
        { key: 'status', label: 'Status', isDefault: true, render: (val, row) => row.attributes?.status || 'Active' },
        { key: 'phone', label: 'Phone', render: (val, row) => row.attributes?.phone || '-' },
        { key: 'email', label: 'Email', render: (val, row) => row.attributes?.email || '-' },
        { key: 'website', label: 'Website', render: (val, row) => row.attributes?.website || '-' },
        { key: 'created_at', label: 'Created At', render: (val) => val ? new Date(val).toLocaleDateString() : '-' },
        { key: 'updated_at', label: 'Updated At', render: (val) => val ? new Date(val).toLocaleDateString() : '-' }
      ],
      fields: [
        { name: 'name', label: 'Company Name', required: true },
        { name: 'domain', label: 'Domain' },
        { name: 'industry', label: 'Industry' },
        { name: 'tier', label: 'Tier', type: 'select', options: [{value:'standard',label:'Standard'},{value:'premium',label:'Premium'},{value:'enterprise',label:'Enterprise'}] },
        { name: 'status', label: 'Status', type: 'select', options: [{value:'Active',label:'Active'},{value:'Inactive',label:'Inactive'}] },
        { name: 'phone', label: 'Phone' },
        { name: 'email', label: 'Email', type: 'email' },
        { name: 'address', label: 'Address' },
        { name: 'website', label: 'Website' }
      ],
      filters: [
        { name: 'industry', label: 'Industry', options: [{value:'Technology',label:'Technology'},{value:'Finance',label:'Finance'},{value:'Retail',label:'Retail'}] },
        { name: 'tier', label: 'Tier', options: [{value:'standard',label:'Standard'},{value:'premium',label:'Premium'},{value:'enterprise',label:'Enterprise'}] },
        { name: 'status', label: 'Status', options: [{value:'Active',label:'Active'},{value:'Inactive',label:'Inactive'}] }
      ]
    },
    opportunities: {
      title: 'Opportunities',
      fetchFn: () => horizonApi.getDeals(),
      createFn: (data) => {
        const payload = { ...data, lost_reason: data.description };
        return horizonApi.createDeal(payload);
      },
      updateFn: (id, data) => {
        const payload = { ...data, lost_reason: data.description };
        return horizonApi.updateDeal(id, payload);
      },
      deleteFn: (id) => horizonApi.deleteDeal(id),
      columns: [
        { key: 'title', label: 'Deal Name', isDefault: true },
        { key: 'account_name', label: 'Company/Customer', isDefault: true, render: (val, row) => row.account_name || '-' },
        { key: 'stage', label: 'Stage', isDefault: true, render: (val) => <span className="capitalize">{val}</span> },
        { key: 'value', label: 'Amount', isDefault: true, render: (val) => `$${parseFloat(val || 0).toLocaleString()}` },
        { key: 'expected_close_date', label: 'Expected Close', isDefault: true, render: (val) => val ? new Date(val).toLocaleDateString() : '-' },
        { key: 'owner_username', label: 'Owner', render: (val) => val || '-' },
        { key: 'probability', label: 'Probability (%)', render: (val) => `${val || 0}%` },
        { key: 'created_at', label: 'Created At', render: (val) => val ? new Date(val).toLocaleDateString() : '-' }
      ],
      fields: [
        { name: 'title', label: 'Deal Name', required: true },
        { name: 'account', label: 'Company', type: 'select', source: 'companies' },
        { name: 'stage', label: 'Stage', type: 'select', options: [
            { value: 'visitor', label: 'Visitor' },
            { value: 'lead', label: 'Lead' },
            { value: 'opportunity', label: 'Opportunity' },
            { value: 'proposal', label: 'Proposal' },
            { value: 'won', label: 'Won' },
            { value: 'lost', label: 'Lost' }
        ]},
        { name: 'value', label: 'Amount', type: 'number', required: true },
        { name: 'expected_close_date', label: 'Expected Close Date', type: 'date' },
        { name: 'description', label: 'Description' }
      ],
      filters: [
        { name: 'stage', label: 'Stage', options: [
            { value: 'visitor', label: 'Visitor' },
            { value: 'lead', label: 'Lead' },
            { value: 'opportunity', label: 'Opportunity' },
            { value: 'proposal', label: 'Proposal' },
            { value: 'won', label: 'Won' },
            { value: 'lost', label: 'Lost' }
        ]},
        { name: 'account', label: 'Company', source: 'companies' }
      ]
    },
    employees: {
      title: 'Employees',
      fetchFn: () => horizonApi.getEmployees(),
      createFn: (data) => horizonApi.createEmployee(data),
      updateFn: (id, data) => horizonApi.updateEmployee(id, data),
      deleteFn: (id) => horizonApi.deleteEmployee(id),
      columns: [
        { key: 'name', label: 'Name', isDefault: true, render: (val, row) => `${row.first_name} ${row.last_name}` },
        { key: 'email', label: 'Email', isDefault: true },
        { key: 'role', label: 'Role', isDefault: true },
        { key: 'department', label: 'Department', isDefault: true, render: (val) => val || '-' },
        { key: 'status', label: 'Status', isDefault: true, render: (val) => (
          <span className={`px-2 py-1 text-xs rounded-full ${val === 'active' ? 'bg-green-100 text-green-700' : val === 'on_leave' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
            <span className="capitalize">{String(val || '').replace('_', ' ')}</span>
          </span>
        ) },
        { key: 'phone', label: 'Phone', render: (_val, row) => row.phone || '-' },
        { key: 'joining_date', label: 'Joining Date', render: (_val, row) => row.joining_date || '-' },
        { key: 'created_at', label: 'Created At', render: (val) => val ? new Date(val).toLocaleDateString() : '-' }
      ],
      fields: [
        { name: 'first_name', label: 'First Name', required: true },
        { name: 'last_name', label: 'Last Name', required: true },
        { name: 'email', label: 'Email', type: 'email', required: true },
        { name: 'role', label: 'Role / Job Title', required: true },
        { name: 'status', label: 'Status', type: 'select', options: [
            { value: 'active', label: 'Active' },
            { value: 'on_leave', label: 'On Leave' },
            { value: 'terminated', label: 'Terminated' }
        ]}
      ],
      filters: [
        { name: 'status', label: 'Status', options: [
            { value: 'active', label: 'Active' },
            { value: 'on_leave', label: 'On Leave' },
            { value: 'terminated', label: 'Terminated' }
        ]}
      ]
    },
    products: {
      title: 'Products',
      fetchFn: () => horizonApi.getProducts(),
      createFn: (data) => {
        const payload = { ...data, is_active: data.is_active === 'true' || data.is_active === true };
        return horizonApi.createProduct(payload);
      },
      updateFn: (id, data) => {
        const payload = { ...data, is_active: data.is_active === 'true' || data.is_active === true };
        return horizonApi.updateProduct(id, payload);
      },
      deleteFn: (id) => horizonApi.deleteProduct(id),
      columns: [
        { key: 'name', label: 'Product Name', isDefault: true },
        { key: 'sku', label: 'SKU', isDefault: true, render: (val) => val || '-' },
        { key: 'price', label: 'Price', isDefault: true, render: (val) => `$${parseFloat(val || 0).toLocaleString()}` },
        { key: 'is_active', label: 'Status', isDefault: true, render: (val) => (
          <span className={`px-2 py-1 text-xs rounded-full ${val ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {val ? 'Active' : 'Inactive'}
          </span>
        ) },
        { key: 'category', label: 'Category', render: (_val, row) => row.category || '-' },
        { key: 'description', label: 'Description', render: (val) => val || '-' },
        { key: 'created_at', label: 'Created At', render: (val) => val ? new Date(val).toLocaleDateString() : '-' },
        { key: 'updated_at', label: 'Updated At', render: (val) => val ? new Date(val).toLocaleDateString() : '-' }
      ],
      fields: [
        { name: 'name', label: 'Product Name', required: true },
        { name: 'sku', label: 'SKU' },
        { name: 'price', label: 'Price', type: 'number', required: true },
        { name: 'description', label: 'Description' },
        { name: 'is_active', label: 'Status', type: 'select', options: [
            { value: 'true', label: 'Active' },
            { value: 'false', label: 'Inactive' }
        ]}
      ],
      filters: [
        { name: 'is_active', label: 'Status', options: [
            { value: 'true', label: 'Active' },
            { value: 'false', label: 'Inactive' }
        ]}
      ]
    }
  };

  const config = configs[entity];
  
  // Custom Columns Logic
  const localStorageKey = `crm_columns_${entity}`;
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);

  useEffect(() => {
    const saved = localStorage.getItem(localStorageKey);
    if (saved) {
      setSelectedColumns(JSON.parse(saved));
    } else {
      setSelectedColumns(config.columns.filter(c => c.isDefault).map(c => c.key));
    }
  }, [entity]);

  const handleColumnToggle = (key: string) => {
    let newCols = [...selectedColumns];
    if (newCols.includes(key)) {
      newCols = newCols.filter(c => c !== key);
    } else {
      // maintain order based on config
      const allKeys = config.columns.map(c => c.key);
      newCols.push(key);
      newCols.sort((a, b) => allKeys.indexOf(a) - allKeys.indexOf(b));
    }
    setSelectedColumns(newCols);
  };

  const applyColumns = () => {
    localStorage.setItem(localStorageKey, JSON.stringify(selectedColumns));
    setShowCustomize(false);
  };
  
  const resetColumns = () => {
    const def = config.columns.filter(c => c.isDefault).map(c => c.key);
    setSelectedColumns(def);
    localStorage.setItem(localStorageKey, JSON.stringify(def));
    setShowCustomize(false);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const result = await config.fetchFn();
      const dataList = Array.isArray(result) ? result : (result?.results || []);
      setData(dataList);
    } catch (error) {
      console.error(`Failed to fetch ${entity}:`, error);
      setData([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadData();
    setCurrentPage(1);
    setSearch('');
    setActiveFilters({});
  }, [entity]);

  // Filtering based on search text AND active filters
  const filteredData = useMemo(() => {
    return data.filter((row) => {
      // 1. Text Search
      if (search) {
        const searchLower = search.toLowerCase();
        const matchesSearch = config.columns.some(col => {
          let val = row[col.key];
          if (entity === 'customers' && row.attributes) {
            if (col.key === 'first_name') val = val || row.attributes.firstName;
            if (col.key === 'last_name') val = val || row.attributes.lastName;
          }
          if (entity === 'companies' && row.attributes && row.attributes[col.key]) {
             val = row.attributes[col.key];
          }
          if (val === null || val === undefined) return false;
          return String(val).toLowerCase().includes(searchLower);
        });
        if (!matchesSearch) return false;
      }
      
      // 2. Active Filters
      for (const [fKey, fVal] of Object.entries(activeFilters)) {
        if (!fVal) continue;
        let rowVal = row[fKey];
        if (entity === 'customers' && fKey === 'status' && row.attributes) {
            rowVal = row.attributes.status;
        }
        if (entity === 'companies' && fKey === 'status' && row.attributes) {
            rowVal = row.attributes.status;
        }
        if (String(rowVal) !== String(fVal)) return false;
      }

      return true;
    });
  }, [data, search, activeFilters, entity, config.columns]);

  const totalPages = Math.ceil(filteredData.length / itemsPerPage);
  const paginatedData = filteredData.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const activeFiltersCount = Object.values(activeFilters).filter(Boolean).length;

  const handleExportCSV = () => {
    if (filteredData.length === 0) return;
    const exportCols = config.columns.filter(c => selectedColumns.includes(c.key));
    const header = exportCols.map(c => c.label).join(',');
    const rows = filteredData.map(row => 
      exportCols.map(col => {
        let val = row[col.key];
        if (row.attributes) {
            if (col.key === 'first_name') val = val || row.attributes.firstName;
            if (col.key === 'last_name') val = val || row.attributes.lastName;
            if (entity === 'companies' && row.attributes[col.key]) val = row.attributes[col.key];
            if (col.key === 'status') val = val || row.attributes.status;
        }
        if (val === null || val === undefined) val = '';
        return `"${String(val).replace(/"/g, '""')}"`;
      }).join(',')
    );
    const csvContent = [header, ...rows].join('\\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${entity}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const openModal = (mode: 'create' | 'edit' | 'view', record: any = null) => {
    setModalMode(mode);
    setSelectedRecord(record);
    if (mode === 'create') {
      setFormData({});
    } else {
      // populate form data
      const initData: any = {};
      config.fields.forEach(f => {
        initData[f.name] = record[f.name] ?? '';
        if (entity === 'customers' && record.attributes) {
          if (f.name === 'first_name') initData[f.name] = record.first_name || record.attributes.firstName || '';
          if (f.name === 'last_name') initData[f.name] = record.last_name || record.attributes.lastName || '';
          if (f.name === 'status') initData[f.name] = record.attributes.status || '';
        }
        if (entity === 'companies' && record.attributes) {
          if (f.name === 'phone') initData[f.name] = record.attributes.phone || '';
          if (f.name === 'email') initData[f.name] = record.attributes.email || '';
          if (f.name === 'address') initData[f.name] = record.attributes.address || '';
          if (f.name === 'website') initData[f.name] = record.attributes.website || '';
          if (f.name === 'status') initData[f.name] = record.attributes.status || '';
        }
        if (entity === 'opportunities') {
          if (f.name === 'description') initData[f.name] = record.lost_reason || '';
        }
      });
      if (entity === 'customers' && record.account) {
        initData['company'] = record.account;
      }
      if (entity === 'products' && record.is_active !== undefined) {
          initData['is_active'] = record.is_active ? 'true' : 'false';
      }
      setFormData(initData);
    }
    setErrorMsg('');
    setSuccessMsg('');
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev: any) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    try {
      if (modalMode === 'create') {
        await config.createFn(formData);
        setSuccessMsg(`Successfully created ${config.title.endsWith('ies') ? config.title.slice(0, -3) + 'y' : config.title.slice(0, -1)}`);
      } else if (modalMode === 'edit' && selectedRecord) {
        await config.updateFn(selectedRecord.id, formData);
        setSuccessMsg(`Successfully updated ${config.title.endsWith('ies') ? config.title.slice(0, -3) + 'y' : config.title.slice(0, -1)}`);
      }
      loadData();
      setTimeout(() => {
        closeModal();
      }, 1000);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || JSON.stringify(err.response?.data) || err.message || 'An error occurred.');
    }
  };

  const handleDelete = async (id: string | number) => {
    if (window.confirm('Delete this record?\\n\\nThis action cannot be undone.')) {
      try {
        await config.deleteFn(id);
        setSuccessMsg('Record deleted successfully');
        loadData();
      } catch (err: any) {
        alert('Failed to delete: ' + (err.response?.data?.detail || JSON.stringify(err.response?.data) || err.message));
      }
    }
  };

  const getSourceOptions = (source?: string) => {
    if (source === 'companies') return relCompanies.map(c => ({ value: c.id, label: c.name }));
    if (source === 'customers') return relCustomers.map(c => ({ value: c.id, label: `${c.first_name || ''} ${c.last_name || ''}`.trim() || c.primary_email }));
    if (source === 'employees') return relEmployees.map(c => ({ value: c.id, label: `${c.first_name} ${c.last_name}` }));
    return [];
  };

  const activeColumns = config.columns.filter(c => selectedColumns.includes(c.key));

  return (
    <div className="flex-1 p-8 bg-gray-50 h-full flex flex-col relative">
      {successMsg && !modalOpen && (
        <div className="absolute top-4 right-8 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded z-50 shadow-sm flex items-center gap-2">
          {successMsg}
        </div>
      )}
      
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 capitalize">{config.title}</h1>
          <p className="text-sm text-gray-500">Universal CRM Core • Interconnected Relational Data</p>
        </div>
        <div className="flex gap-3">
          <button onClick={loadData} className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
             <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-brand-600' : ''}`} />
          </button>
          <button onClick={handleExportCSV} className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">
            <Download className="w-4 h-4" /> Export CSV
          </button>
          <button onClick={() => openModal('create')} className="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 shadow-sm">
            <Plus className="w-4 h-4" /> Add {config.title.endsWith('ies') ? config.title.slice(0, -3) + 'y' : config.title.slice(0, -1)}
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex-1 flex flex-col overflow-hidden">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-white">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input 
              type="text" 
              placeholder={`Search ${config.title.toLowerCase()}...`}
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setCurrentPage(1);
              }}
              className="pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm w-72 focus:outline-none focus:ring-2 focus:ring-brand-500 transition-shadow"
            />
          </div>
          
          <div className="flex items-center gap-3 relative">
            <div className="relative" ref={filterRef}>
              <button 
                onClick={() => setShowFilter(!showFilter)}
                className={`flex items-center gap-2 px-3 py-2 border ${activeFiltersCount > 0 ? 'border-brand-500 text-brand-700 bg-brand-50' : 'border-gray-300 text-gray-600 hover:bg-gray-50'} rounded-lg text-sm font-medium transition-colors`}
              >
                <Filter className="w-4 h-4" /> Filter {activeFiltersCount > 0 && `(${activeFiltersCount})`}
              </button>
              
              {showFilter && (
                <div className="absolute right-0 mt-2 w-72 bg-white border border-gray-200 rounded-xl shadow-xl z-20 p-4">
                  <h3 className="font-semibold text-gray-900 mb-3 text-sm">Filters</h3>
                  <div className="space-y-4">
                    {config.filters.map(f => (
                      <div key={f.name}>
                        <label className="block text-xs font-medium text-gray-700 mb-1">{f.label}</label>
                        <select
                          className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-brand-500"
                          value={activeFilters[f.name] || ''}
                          onChange={(e) => setActiveFilters(p => ({...p, [f.name]: e.target.value}))}
                        >
                          <option value="">All</option>
                          {(f.options || getSourceOptions(f.source)).map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                          ))}
                        </select>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 flex gap-2 pt-3 border-t border-gray-100">
                    <button 
                      onClick={() => { setActiveFilters({}); setShowFilter(false); }}
                      className="flex-1 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded border border-gray-300"
                    >
                      Clear
                    </button>
                    <button 
                      onClick={() => setShowFilter(false)}
                      className="flex-1 px-3 py-1.5 text-sm text-white bg-brand-600 hover:bg-brand-700 rounded"
                    >
                      Apply
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="relative" ref={customizeRef}>
              <button 
                onClick={() => setShowCustomize(!showCustomize)}
                className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 font-medium"
              >
                <Settings2 className="w-4 h-4" /> Customize
              </button>
              
              {showCustomize && (
                <div className="absolute right-0 mt-2 w-64 bg-white border border-gray-200 rounded-xl shadow-xl z-20 p-4">
                  <h3 className="font-semibold text-gray-900 mb-3 text-sm">Customize Columns</h3>
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
                    {config.columns.map(col => (
                      <label key={col.key} className="flex items-center gap-2 cursor-pointer group">
                        <input 
                          type="checkbox" 
                          checked={selectedColumns.includes(col.key)}
                          onChange={() => handleColumnToggle(col.key)}
                          className="rounded border-gray-300 text-brand-600 focus:ring-brand-500 w-4 h-4"
                        />
                        <span className="text-sm text-gray-700 group-hover:text-gray-900">{col.label}</span>
                      </label>
                    ))}
                  </div>
                  <div className="mt-4 flex gap-2 pt-3 border-t border-gray-100">
                    <button 
                      onClick={resetColumns}
                      className="flex-1 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded border border-gray-300"
                    >
                      Reset
                    </button>
                    <button 
                      onClick={applyColumns}
                      className="flex-1 px-3 py-1.5 text-sm text-white bg-brand-600 hover:bg-brand-700 rounded"
                    >
                      Apply
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex-1 overflow-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-gray-50 sticky top-0 z-10 border-b border-gray-200">
              <tr>
                <th className="w-12 px-4 py-3 text-gray-400 font-normal border-r border-gray-200 bg-gray-100 text-center text-xs">#</th>
                <th className="w-12 px-6 py-3 border-r border-gray-100">
                  <input type="checkbox" className="rounded border-gray-300 text-brand-600 focus:ring-brand-500" />
                </th>
                {activeColumns.map(col => (
                  <th key={col.key} className="px-6 py-3 font-medium text-gray-600">
                    {col.label}
                  </th>
                ))}
                <th className="px-6 py-3 font-medium text-gray-600 text-right sticky right-0 bg-gray-50 border-l border-gray-200">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {loading ? (
                <tr>
                  <td colSpan={activeColumns.length + 3} className="px-6 py-12 text-center text-gray-400">
                    <div className="flex flex-col items-center justify-center">
                      <RefreshCw className="w-6 h-6 animate-spin mb-2 text-brand-500" />
                      Loading records...
                    </div>
                  </td>
                </tr>
              ) : paginatedData.length === 0 ? (
                <tr>
                  <td colSpan={activeColumns.length + 3} className="px-6 py-16 text-center text-gray-500">
                    {search || activeFiltersCount > 0 ? (
                      <div className="flex flex-col items-center justify-center">
                        <Search className="w-8 h-8 text-gray-300 mb-3" />
                        <p className="text-gray-900 font-medium mb-1">No matching records</p>
                        <p className="text-sm text-gray-500">Try clearing your filters or search query.</p>
                        <button onClick={() => { setSearch(''); setActiveFilters({}); }} className="mt-4 text-brand-600 hover:text-brand-700 font-medium text-sm">Clear Filters</button>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center">
                        <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-3">
                          {entity === 'companies' ? <Building2 className="text-gray-400" /> : entity === 'customers' ? <User className="text-gray-400" /> : entity === 'opportunities' ? <Briefcase className="text-gray-400" /> : <Package className="text-gray-400" />}
                        </div>
                        <p className="text-gray-900 font-medium mb-1">No {entity} found</p>
                        <p className="text-sm text-gray-500 mb-4">Create your first record to get started.</p>
                        <button onClick={() => openModal('create')} className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700">
                           + Add {config.title.endsWith('ies') ? config.title.slice(0, -3) + 'y' : config.title.slice(0, -1)}
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ) : (
                paginatedData.map((row, idx) => (
                  <tr key={row.id || idx} className="hover:bg-brand-50/30 transition-colors group">
                    <td className="px-4 py-3 text-center text-gray-400 text-xs font-mono border-r border-gray-100">
                      {(currentPage - 1) * itemsPerPage + idx + 1}
                    </td>
                    <td className="px-6 py-3 border-r border-gray-100">
                      <input type="checkbox" className="rounded border-gray-300 text-brand-600 focus:ring-brand-500" />
                    </td>
                    {activeColumns.map(col => (
                      <td key={col.key} className="px-6 py-3 text-gray-700 text-sm">
                        {col.render ? col.render(row[col.key], row) : row[col.key] || '-'}
                      </td>
                    ))}
                    <td className="px-6 py-3 text-right sticky right-0 bg-white group-hover:bg-brand-50/10 border-l border-gray-100">
                      <div className="flex justify-end items-center gap-4">
                        <button onClick={() => openModal('view', row)} className="text-gray-400 hover:text-brand-600" title="View Profile">
                          <Eye className="w-4 h-4" />
                        </button>
                        <button onClick={() => openModal('edit', row)} className="text-gray-400 hover:text-blue-600" title="Edit">
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button onClick={() => handleDelete(row.id)} className="text-gray-400 hover:text-red-600" title="Delete">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        <div className="px-6 py-3 border-t border-gray-200 flex justify-between items-center text-sm text-gray-500 bg-white">
          <span>Showing {paginatedData.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0}–{Math.min(currentPage * itemsPerPage, filteredData.length)} of {filteredData.length} records</span>
          <div className="flex items-center gap-2">
            <button 
              disabled={currentPage === 1} 
              onClick={() => setCurrentPage(p => p - 1)}
              className="px-3 py-1.5 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:hover:bg-transparent transition-colors">
              Previous
            </button>
            <button 
              disabled={currentPage === totalPages || totalPages === 0}
              onClick={() => setCurrentPage(p => p + 1)}
              className="px-3 py-1.5 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:hover:bg-transparent transition-colors">
              Next
            </button>
          </div>
        </div>
      </div>

      {modalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[95vh] border border-gray-200">
            <div className="flex justify-between items-center p-5 border-b border-gray-100 bg-gray-50/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-brand-100 text-brand-600 flex items-center justify-center">
                  {entity === 'companies' ? <Building2 className="w-5 h-5" /> : entity === 'customers' || entity === 'employees' ? <User className="w-5 h-5" /> : entity === 'opportunities' ? <Briefcase className="w-5 h-5" /> : <Package className="w-5 h-5" />}
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900 capitalize leading-tight">
                    {modalMode === 'create' ? 'Add ' : modalMode === 'edit' ? 'Edit ' : ''}
                    {modalMode === 'view' ? (selectedRecord.name || selectedRecord.title || `${selectedRecord.first_name || ''} ${selectedRecord.last_name || ''}`.trim() || selectedRecord.primary_email || 'Profile') : config.title.endsWith('ies') ? config.title.slice(0, -3) + 'y' : config.title.slice(0, -1)}
                  </h2>
                  {modalMode === 'view' && <p className="text-xs text-gray-500 mt-0.5 capitalize">{config.title.endsWith('ies') ? config.title.slice(0, -3) + 'y' : config.title.slice(0, -1)} Profile</p>}
                </div>
              </div>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600 bg-white border border-gray-200 rounded-full p-1.5 shadow-sm transition-transform hover:scale-105">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto flex-1 custom-scrollbar">
              {errorMsg && (
                <div className="mb-5 bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded shadow-sm text-sm whitespace-pre-wrap">
                  {errorMsg}
                </div>
              )}
              {successMsg && (
                <div className="mb-5 bg-green-50 border-l-4 border-green-500 text-green-700 p-4 rounded shadow-sm text-sm">
                  {successMsg}
                </div>
              )}
              
              {modalMode === 'view' ? (
                <div className="space-y-8">
                  {/* Basic Profile view layout */}
                  <div>
                    <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4 border-b border-gray-100 pb-2">Basic Information</h3>
                    <div className="grid grid-cols-2 gap-y-4 gap-x-8">
                      {config.fields.slice(0, Math.ceil(config.fields.length / 2)).map(field => (
                        <div key={field.name}>
                          <p className="text-sm font-medium text-gray-500 mb-1">{field.label}</p>
                          <p className="text-base text-gray-900 font-medium">
                            {field.source ? 
                              (getSourceOptions(field.source).find(opt => String(opt.value) === String(formData[field.name]))?.label || formData[field.name] || '-')
                            : (formData[field.name] || '-')}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4 border-b border-gray-100 pb-2">Additional Details</h3>
                    <div className="grid grid-cols-2 gap-y-4 gap-x-8">
                      {config.fields.slice(Math.ceil(config.fields.length / 2)).map(field => (
                        <div key={field.name}>
                          <p className="text-sm font-medium text-gray-500 mb-1">{field.label}</p>
                          <p className="text-base text-gray-900 font-medium break-words">
                            {field.source ? 
                              (getSourceOptions(field.source).find(opt => String(opt.value) === String(formData[field.name]))?.label || formData[field.name] || '-')
                            : (formData[field.name] || '-')}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4 border-b border-gray-100 pb-2">System</h3>
                    <div className="grid grid-cols-2 gap-y-4 gap-x-8">
                      <div>
                        <p className="text-sm font-medium text-gray-500 mb-1">Created At</p>
                        <p className="text-sm text-gray-900">{selectedRecord?.created_at ? new Date(selectedRecord.created_at).toLocaleString() : '-'}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-500 mb-1">Updated At</p>
                        <p className="text-sm text-gray-900">{selectedRecord?.updated_at ? new Date(selectedRecord.updated_at).toLocaleString() : '-'}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <form id="crud-form" onSubmit={handleSubmit} className="grid grid-cols-2 gap-5">
                  {config.fields.map((field) => (
                    <div key={field.name} className={field.type === 'textarea' ? 'col-span-2' : 'col-span-1'}>
                      <label className="block text-sm font-medium text-gray-700 mb-1.5">
                        {field.label} {field.required && <span className="text-red-500">*</span>}
                      </label>
                      {field.type === 'select' ? (
                        <select
                          name={field.name}
                          value={formData[field.name] || ''}
                          onChange={handleInputChange}
                          required={field.required}
                          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 text-gray-900 bg-white shadow-sm transition-all"
                        >
                          <option value="">Select...</option>
                          {(field.options || getSourceOptions(field.source)).map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                          ))}
                        </select>
                      ) : (
                        <input
                          type={field.type || 'text'}
                          name={field.name}
                          value={formData[field.name] || ''}
                          onChange={handleInputChange}
                          required={field.required}
                          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 text-gray-900 shadow-sm transition-all"
                          placeholder={`Enter ${field.label.toLowerCase()}`}
                        />
                      )}
                    </div>
                  ))}
                </form>
              )}
            </div>
            
            <div className="p-5 border-t border-gray-200 flex justify-end gap-3 bg-gray-50 mt-auto">
              {modalMode === 'view' ? (
                <>
                  <button 
                    type="button" 
                    onClick={closeModal} 
                    className="px-5 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-700 font-semibold hover:bg-gray-100 shadow-sm transition-colors"
                  >
                    Close
                  </button>
                  <button 
                    type="button" 
                    onClick={() => setModalMode('edit')}
                    className="px-5 py-2.5 bg-brand-600 text-white rounded-lg text-sm font-semibold hover:bg-brand-700 shadow-sm transition-colors flex items-center gap-2"
                  >
                    <Edit2 className="w-4 h-4" /> Edit Record
                  </button>
                </>
              ) : (
                <>
                  <button 
                    type="button" 
                    onClick={closeModal} 
                    className="px-5 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-700 font-semibold hover:bg-gray-100 shadow-sm transition-colors"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    form="crud-form"
                    className="px-5 py-2.5 bg-brand-600 text-white rounded-lg text-sm font-semibold hover:bg-brand-700 shadow-sm transition-colors"
                  >
                    Save {config.title.endsWith('ies') ? config.title.slice(0, -3) + 'y' : config.title.slice(0, -1)}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
"""

with open("src/pages/CRMCoreListView.tsx", "w") as f:
    f.write(CONTENT)
