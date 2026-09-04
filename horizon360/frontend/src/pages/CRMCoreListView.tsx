import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { horizonApi } from '../api';
import { Download, Search, Plus, Filter } from 'lucide-react';

interface CRMEntityConfig {
  title: string;
  fetchFn: () => Promise<any>;
  columns: { key: string; label: string; render?: (val: any, row: any) => React.ReactNode }[];
}

export const CRMCoreListView = ({ entity }: { entity: 'customers' | 'companies' | 'opportunities' | 'employees' | 'products' }) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const configs: Record<string, CRMEntityConfig> = {
    customers: {
      title: 'Customers',
      fetchFn: () => horizonApi.getCustomers(),
      columns: [
        { key: 'first_name', label: 'First Name', render: (val, row) => val || row.attributes?.firstName || '-' },
        { key: 'last_name', label: 'Last Name', render: (val, row) => val || row.attributes?.lastName || '-' },
        { key: 'primary_email', label: 'Email' },
        { key: 'primary_phone', label: 'Phone No.' },
        { key: 'created_at', label: 'Created At', render: (val) => new Date(val).toLocaleDateString() }
      ]
    },
    companies: {
      title: 'Companies',
      fetchFn: () => horizonApi.getCompanies(),
      columns: [
        { key: 'name', label: 'Company Name' },
        { key: 'domain', label: 'Domain' },
        { key: 'industry', label: 'Industry' },
        { key: 'tier', label: 'Tier' },
      ]
    },
    opportunities: {
      title: 'Opportunities',
      fetchFn: () => horizonApi.getDeals(),
      columns: [
        { key: 'title', label: 'Deal Name' },
        { key: 'stage', label: 'Stage' },
        { key: 'value', label: 'Amount', render: (val) => `$${parseFloat(val).toLocaleString()}` },
        { key: 'created_at', label: 'Created At', render: (val) => new Date(val).toLocaleDateString() }
      ]
    },
    employees: {
      title: 'Employees',
      fetchFn: () => horizonApi.getEmployees(),
      columns: [
        { key: 'first_name', label: 'First Name' },
        { key: 'last_name', label: 'Last Name' },
        { key: 'email', label: 'Email' },
        { key: 'role', label: 'Role' },
        { key: 'status', label: 'Status' }
      ]
    },
    products: {
      title: 'Products',
      fetchFn: () => horizonApi.getProducts(),
      columns: [
        { key: 'name', label: 'Product Name' },
        { key: 'sku', label: 'SKU' },
        { key: 'price', label: 'Price', render: (val) => `$${parseFloat(val).toLocaleString()}` },
      ]
    }
  };

  const config = configs[entity];

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const result = await config.fetchFn();
        // Handle Django Rest Framework pagination format if present
        const dataList = Array.isArray(result) ? result : (result?.results || []);
        setData(dataList);
      } catch (error) {
        console.error(`Failed to fetch ${entity}:`, error);
        setData([]);
      }
      setLoading(false);
    };
    loadData();
  }, [entity]);

  return (
    <div className="flex-1 p-8 bg-gray-50 h-full flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 capitalize">{config.title}</h1>
          <p className="text-sm text-gray-500">Universal CRM Core • Interconnected Relational Data</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">
            <Download className="w-4 h-4" /> Export CSV
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700">
            <Plus className="w-4 h-4" /> Create {config.title.slice(0, -1)}
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex-1 flex flex-col overflow-hidden">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input 
              type="text" 
              placeholder={`Search ${config.title.toLowerCase()}...`}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <button className="flex items-center gap-2 px-3 py-1.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
            <Filter className="w-4 h-4" /> Filter
          </button>
        </div>
        
        <div className="flex-1 overflow-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-gray-50 sticky top-0 z-10 border-b border-gray-200">
              <tr>
                <th className="w-12 px-4 py-3 text-gray-400 font-normal border-r border-gray-200 bg-gray-100 text-center text-xs">
                  #
                </th>
                <th className="w-12 px-6 py-3">
                  <input type="checkbox" className="rounded border-gray-300 text-brand-600 focus:ring-brand-500" />
                </th>
                {config.columns.map(col => (
                  <th key={col.key} className="px-6 py-3 font-medium text-gray-500">
                    {col.label}
                  </th>
                ))}
                <th className="px-6 py-3 font-medium text-gray-500 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={config.columns.length + 3} className="px-6 py-12 text-center text-gray-500">
                    Loading {config.title.toLowerCase()}...
                  </td>
                </tr>
              ) : data.length === 0 ? (
                <tr>
                  <td colSpan={config.columns.length + 3} className="px-6 py-12 text-center text-gray-500">
                    No records found. Data is uniformly synced from Level 2 CDP.
                  </td>
                </tr>
              ) : (
                data.map((row, idx) => (
                  <tr key={row.id || idx} className="hover:bg-gray-50 cursor-pointer">
                    <td className="px-4 py-4 text-center text-gray-400 text-xs font-mono border-r border-gray-200 bg-gray-50">
                      {idx + 1}
                    </td>
                    <td className="px-6 py-4">
                      <input type="checkbox" className="rounded border-gray-300 text-brand-600 focus:ring-brand-500" />
                    </td>
                    {config.columns.map(col => (
                      <td key={col.key} className="px-6 py-4 text-gray-900">
                        {col.render ? col.render(row[col.key], row) : row[col.key] || '-'}
                      </td>
                    ))}
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end items-center gap-3">
                        {entity === 'customers' ? (
                          <Link to={`/crm/customers/${row.id}`} className="text-brand-600 hover:text-brand-800 text-sm font-medium">View</Link>
                        ) : (
                          <button className="text-brand-600 hover:text-brand-800 text-sm font-medium">View</button>
                        )}
                        <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">Edit</button>
                        <button className="text-red-600 hover:text-red-800 text-sm font-medium">Delete</button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        <div className="px-6 py-4 border-t border-gray-200 flex justify-between items-center text-sm text-gray-500 bg-gray-50">
          <span>Showing {data.length} records</span>
          <div className="flex items-center gap-2">
            <button className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-50">Previous</button>
            <button className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-50">Next</button>
          </div>
        </div>
      </div>
    </div>
  );
};
