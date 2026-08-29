import React, { useEffect, useState } from 'react';
import { StatCard } from '../components/StatCard';
import { CustomerTable } from '../components/CustomerTable';
import { horizonApi } from '../api';

export const Dashboard = () => {
  const [customers, setCustomers] = useState([]);
  const [deals, setDeals] = useState([]);
  
  useEffect(() => {
    horizonApi.getCustomers().then(data => setCustomers(data)).catch(console.error);
    horizonApi.getDeals().then(data => setDeals(data)).catch(console.error);
  }, []);

  const unifiedProfilesCount = customers.length;
  const totalEvents = customers.reduce((sum, c: any) => sum + (c.timeline?.length || 0), 0);
  const totalDealValue = deals.reduce((sum, d: any) => sum + parseFloat(d.value || 0), 0);

  return (
    <div className="flex-1 flex flex-col h-full bg-white">
      {/* Top Header */}
      <header className="h-14 border-b border-gray-200 flex items-center px-8 justify-between">
         <div className="flex items-center text-sm text-gray-500">
           <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span> All systems operational
         </div>
         <div className="flex items-center gap-4">
            <input type="text" placeholder="Search resources..." className="bg-gray-100 text-sm rounded px-3 py-1.5 w-64 border-transparent focus:bg-white focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none" />
         </div>
      </header>

      {/* Main Content Area */}
      <div className="p-8 max-w-6xl w-full">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900">Unified Profiles & CRM</h2>
          <p className="text-gray-500 mt-1">Explore and manage unified customer identities across all integrated sources.</p>
        </div>

        {/* Connected Stat Cards */}
        <div className="flex mb-10 rounded-lg shadow-sm">
          <div className="flex-1">
            <StatCard title="Unified Profiles" value={unifiedProfilesCount.toString()} subtext="Total customers" />
          </div>
          <div className="flex-1">
            <StatCard title="Pipeline Value" value={`$${totalDealValue.toFixed(2)}`} subtext={`${deals.length} active deals`} isPositive={true} />
          </div>
          <div className="flex-1">
            <StatCard title="Data Sources" value="1 Active" subtext="Webhook Ingestion" isPositive={true} />
          </div>
          <div className="flex-1">
            <StatCard title="System Health" value="100%" subtext="All systems operational" isPositive={true} />
          </div>
        </div>

        <div>
          <CustomerTable customers={customers} />
        </div>
      </div>
    </div>
  );
};
