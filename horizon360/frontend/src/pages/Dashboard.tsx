import React, { useEffect, useState } from 'react';
import { CustomerTable } from '../components/CustomerTable';
import { horizonApi } from '../api';
import { Link } from 'react-router-dom';

export const Dashboard = () => {
  const [customers, setCustomers] = useState<any[]>([]);
  const [deals, setDeals] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [tickets, setTickets] = useState<any[]>([]);
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  
  const loadDashboardData = () => {
    horizonApi.getCustomers().then(data => setCustomers(data)).catch(console.error);
    horizonApi.getDeals().then(data => setDeals(data)).catch(console.error);
    horizonApi.getEvents().then(data => setEvents(data.slice(0, 10))).catch(console.error);
    horizonApi.getServiceTickets().then(data => setTickets(data)).catch(console.error);
    horizonApi.getCampaigns().then(data => setCampaigns(data)).catch(console.error);
    horizonApi.getProjects().then(data => setProjects(data)).catch(console.error);
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const totalCustomers = customers.length;
  const activeOpportunities = deals.filter(d => d.stage !== 'won' && d.stage !== 'lost').length;
  const pipelineValue = deals.filter(d => d.stage !== 'won' && d.stage !== 'lost').reduce((sum, d) => sum + parseFloat(d.value || 0), 0);
  const wonRevenue = deals.filter(d => d.stage === 'won').reduce((sum, d) => sum + parseFloat(d.value || 0), 0);
  const openTickets = tickets.filter(t => t.status === 'open' || t.status === 'in_progress').length;
  const activeCampaigns = campaigns.filter(c => c.status === 'active').length;
  const activeProjects = projects.filter(p => p.status === 'active').length;

  return (
    <div className="flex-1 flex flex-col h-full bg-white overflow-y-auto">
      {/* Top Header */}
      <header className="h-14 border-b border-gray-200 flex items-center px-8 justify-between shrink-0">
         <div className="flex items-center text-sm font-semibold text-gray-700">
           CRM Dashboard
         </div>
         <div className="flex items-center gap-4">
            <input type="text" placeholder="Search CRM..." className="bg-gray-100 text-sm rounded px-3 py-1.5 w-64 border-transparent focus:bg-white focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none" />
         </div>
      </header>

      {/* Main Content Area */}
      <div className="p-8 max-w-6xl w-full">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900">CRM Overview</h2>
          <p className="text-gray-500 mt-1">Manage your customers, sales pipeline, and business operations.</p>
        </div>

        {/* CRM Stats Grid */}
        <div className="grid grid-cols-4 gap-4 mb-10">
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Total Customers</h4>
            <div className="text-2xl font-bold text-gray-900">{totalCustomers}</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Active Opportunities</h4>
            <div className="text-2xl font-bold text-gray-900">{activeOpportunities}</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Pipeline Value</h4>
            <div className="text-2xl font-bold text-brand-600">${pipelineValue.toLocaleString()}</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Won Revenue</h4>
            <div className="text-2xl font-bold text-green-600">${wonRevenue.toLocaleString()}</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Open Tickets</h4>
            <div className="text-2xl font-bold text-orange-600">{openTickets}</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Active Campaigns</h4>
            <div className="text-2xl font-bold text-blue-600">{activeCampaigns}</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Active Projects</h4>
            <div className="text-2xl font-bold text-purple-600">{activeProjects}</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-8 mb-8">
          {/* Recent Activity */}
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
            {events.length === 0 ? (
              <div className="text-gray-500 text-sm">No recent events found.</div>
            ) : (
              <div className="space-y-3">
                {events.map((ev: any) => (
                  <div key={ev.id} className="text-sm flex justify-between items-center border-b border-gray-100 pb-2">
                    <div>
                      <span className="font-medium text-brand-600">{ev.event_name}</span>
                      <div className="text-xs text-gray-500 mt-1">{new Date(ev.created_at).toLocaleString()}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          {/* Recent Opportunities */}
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Opportunities</h3>
            {deals.length === 0 ? (
              <div className="text-gray-500 text-sm">No recent opportunities found.</div>
            ) : (
              <div className="space-y-3">
                {deals.slice(0, 5).map((deal: any) => (
                  <div key={deal.id} className="text-sm flex justify-between items-center border-b border-gray-100 pb-2">
                    <div>
                      <span className="font-medium text-gray-900">{deal.name}</span>
                      <div className="text-xs text-gray-500 mt-1 capitalize">{deal.stage}</div>
                    </div>
                    <div className="font-bold text-brand-600">${parseFloat(deal.value || 0).toLocaleString()}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-4">Customers</h3>
          <CustomerTable customers={customers} />
        </div>
      </div>
    </div>
  );
};
