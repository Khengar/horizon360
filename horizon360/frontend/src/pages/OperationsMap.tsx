import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Database, Users, LayoutDashboard, ShoppingCart, Activity, FileText, Settings, Briefcase, Truck } from 'lucide-react';

export const OperationsMap = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [integrations, setIntegrations] = useState<any[]>([]);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [
          deals, invoices, tickets, campaigns,
          projects, employees, orders, partners,
          vendors, wfs, integs
        ] = await Promise.all([
          horizonApi.getDeals(), horizonApi.getInvoices(), horizonApi.getServiceTickets(), horizonApi.getCampaigns(),
          horizonApi.getProjects(), horizonApi.getEmployees(), horizonApi.getOrders(), horizonApi.getPartners(),
          horizonApi.getVendors(), horizonApi.getWorkflows(), horizonApi.getIntegrations()
        ]);
        
        setData({
          Sales: { records: deals.length, status: 'Operational', path: '/pipeline' },
          Finance: { records: invoices.length, status: 'Operational', path: '/finance' },
          Service: { records: tickets.length, status: 'Operational', path: '/service' },
          Marketing: { records: campaigns.length, status: 'Operational', path: '/marketing' },
          Projects: { records: projects.length, status: 'Operational', path: '/projects' },
          HRMS: { records: employees.length, status: 'Operational', path: '/hrms' },
          Commerce: { records: orders.length, status: 'Operational', path: '/commerce' },
          Partner: { records: partners.length, status: 'Operational', path: '/partner' },
          Vendor: { records: vendors.length, status: 'Operational', path: '/vendor' }
        });
        setWorkflows(wfs);
        setIntegrations(integs);
      } catch (e) {
        console.error("Failed to load operations map data", e);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  const BIOMS = [
    { name: 'Marketing', icon: Activity, color: 'text-pink-600', bg: 'bg-pink-100', border: 'border-pink-200' },
    { name: 'Sales', icon: Briefcase, color: 'text-blue-600', bg: 'bg-blue-100', border: 'border-blue-200' },
    { name: 'Finance', icon: FileText, color: 'text-green-600', bg: 'bg-green-100', border: 'border-green-200' },
    { name: 'Projects', icon: LayoutDashboard, color: 'text-indigo-600', bg: 'bg-indigo-100', border: 'border-indigo-200' },
    { name: 'Service', icon: Settings, color: 'text-gray-600', bg: 'bg-gray-100', border: 'border-gray-200' },
    { name: 'HRMS', icon: Users, color: 'text-orange-600', bg: 'bg-orange-100', border: 'border-orange-200' },
    { name: 'Commerce', icon: ShoppingCart, color: 'text-purple-600', bg: 'bg-purple-100', border: 'border-purple-200' },
    { name: 'Partner', icon: Users, color: 'text-teal-600', bg: 'bg-teal-100', border: 'border-teal-200' },
    { name: 'Vendor', icon: Truck, color: 'text-yellow-600', bg: 'bg-yellow-100', border: 'border-yellow-200' },
  ];

  return (
    <div className="flex-1 p-8 bg-slate-50 h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto">
        <div className="mb-10 text-center">
          <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight mb-4">Horizon 360 Operations Map</h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            The Universal Business Operating System. Real-time visualization of interconnected BIOMs, data records, and automated workflow pathways across the enterprise.
          </p>
        </div>

        {loading ? (
          <div className="text-center py-20 text-slate-500">Initializing Universal Map...</div>
        ) : (
          <>
            {/* Horizon Nexus Layer */}
            <div className="mb-12 bg-indigo-900 rounded-xl p-8 border border-indigo-700 shadow-lg text-white">
              <h2 className="text-2xl font-bold mb-6 text-center text-indigo-100 uppercase tracking-widest">Horizon Nexus Gateway</h2>
              <div className="flex justify-center items-center gap-12">
                {integrations.length === 0 ? (
                  <div className="text-indigo-300">No external integrations configured</div>
                ) : integrations.map(int => (
                  <div key={int.id} className="flex flex-col items-center cursor-pointer" onClick={() => navigate('/integrations')}>
                    <div className="bg-indigo-800 border-2 border-indigo-500 rounded-lg p-4 font-bold text-lg mb-2 shadow-inner">
                      {int.name}
                    </div>
                    <div className="flex flex-col items-center text-indigo-300">
                      <span className="text-[10px] uppercase font-bold tracking-wider">{int.direction}</span>
                      <div className="h-8 border-l-2 border-dashed border-indigo-400 mt-2 mb-2"></div>
                      <ArrowRight className="w-5 h-5 text-indigo-400 rotate-90" />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-8 mb-12 relative z-10">
              {BIOMS.map(biom => {
                const bData = data[biom.name] || { records: 0, status: 'Unknown', path: '/' };
                const entering = workflows.filter(w => w.destination_biom === biom.name && w.is_active);
                const leaving = workflows.filter(w => w.source_biom === biom.name && w.is_active);
                const Icon = biom.icon;

                return (
                  <div 
                    key={biom.name}
                    onClick={() => navigate(bData.path)}
                    className={`bg-white rounded-xl border-2 ${biom.border} shadow-sm p-6 cursor-pointer hover:shadow-md transition-shadow relative overflow-hidden`}
                  >
                    <div className="absolute top-0 right-0 p-4">
                      <span className={`px-2 py-1 text-xs font-bold rounded-full bg-slate-100 text-slate-700`}>
                        {bData.status}
                      </span>
                    </div>
                    <div className="flex items-center space-x-4 mb-4">
                      <div className={`p-3 rounded-lg ${biom.bg} ${biom.color}`}>
                        <Icon className="w-6 h-6" />
                      </div>
                      <h2 className="text-2xl font-bold text-slate-800">{biom.name}</h2>
                    </div>
                    
                    <div className="mb-4">
                      <div className="text-sm text-slate-500 font-semibold uppercase tracking-wider">Primary Records</div>
                      <div className="text-3xl font-black text-slate-800">{bData.records}</div>
                    </div>

                    <div className="flex justify-between items-center border-t border-slate-100 pt-4 mt-4">
                      <div className="text-sm text-slate-600">
                        <span className="font-bold text-slate-900">{entering.length}</span> Workflows In
                      </div>
                      <div className="text-sm text-slate-600">
                        <span className="font-bold text-slate-900">{leaving.length}</span> Workflows Out
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8">
              <h3 className="text-xl font-bold text-slate-800 mb-6 flex items-center">
                <Database className="w-5 h-5 mr-2 text-indigo-600" />
                Active Cross-BIOM Automated Routes
              </h3>
              
              <div className="grid grid-cols-2 gap-6">
                {workflows.filter(w => w.is_active).map(wf => (
                  <div key={wf.id} onClick={() => navigate('/workflows')} className="flex items-center p-4 bg-slate-50 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-100 transition-colors">
                    <div className="flex-1 text-center font-bold text-sm text-slate-700 bg-white border border-slate-200 py-2 rounded shadow-sm">
                      {wf.source_biom || 'External'}
                      <div className="text-xs text-slate-500 font-normal mt-1">{wf.trigger_event}</div>
                    </div>
                    <div className="mx-4 flex flex-col items-center">
                      <ArrowRight className="w-6 h-6 text-indigo-400 mb-1" />
                      <span className="text-[10px] font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">{wf.name}</span>
                    </div>
                    <div className="flex-1 text-center font-bold text-sm text-slate-700 bg-white border border-slate-200 py-2 rounded shadow-sm">
                      {wf.destination_biom || 'External'}
                      <div className="text-xs text-slate-500 font-normal mt-1">{wf.action_type}</div>
                    </div>
                  </div>
                ))}
                {workflows.filter(w => w.is_active).length === 0 && (
                  <div className="col-span-2 text-center text-slate-500 py-8">No active cross-BIOM routes configured.</div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
