import React, { useEffect, useState } from 'react';
import { StatCard } from '../components/StatCard';
import { CustomerTable } from '../components/CustomerTable';
import { horizonApi } from '../api';
import { Link } from 'react-router-dom';
import { Copilot } from '../components/Copilot';

export const Dashboard = () => {
  const [customers, setCustomers] = useState([]);
  const [deals, setDeals] = useState([]);
  const [events, setEvents] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [insights, setInsights] = useState([]);
  
  useEffect(() => {
    horizonApi.getCustomers().then(data => setCustomers(data)).catch(console.error);
    horizonApi.getDeals().then(data => setDeals(data)).catch(console.error);
    horizonApi.getEvents().then(data => setEvents(data.slice(0, 5))).catch(console.error);
    horizonApi.getWorkflowExecutions().then(data => setExecutions(data.slice(0, 5))).catch(console.error);
    horizonApi.getInsights().then(data => setInsights(data)).catch(console.error);
  }, []);

  const unifiedProfilesCount = customers.length;
  const totalDealValue = deals.reduce((sum, d: any) => sum + parseFloat(d.value || 0), 0);
  const wonRevenue = deals.filter((d: any) => d.stage === 'won').reduce((sum, d: any) => sum + parseFloat(d.value || 0), 0);

  return (
    <div className="flex-1 flex flex-col h-full bg-white overflow-y-auto">
      {/* Top Header */}
      <header className="h-14 border-b border-gray-200 flex items-center px-8 justify-between shrink-0">
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
        
        <Copilot />

        {/* Intelligence Center */}
        <div className="mb-10">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Intelligence Center</h3>
          {insights.length === 0 ? (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center text-gray-500 text-sm">
              No new insights or recommendations at this time.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {insights.map((insight: any) => (
                <div key={insight.id} className="bg-white border border-gray-200 rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start mb-3">
                    <span className={`px-2 py-1 text-xs font-semibold rounded ${
                      insight.severity === 'critical' ? 'bg-red-100 text-red-700' :
                      insight.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                      insight.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                      {insight.severity.toUpperCase()} RISK
                    </span>
                    <span className="text-xs text-gray-400">{new Date(insight.created_at).toLocaleDateString()}</span>
                  </div>
                  
                  <h4 className="font-bold text-gray-900 mb-1">{insight.title}</h4>
                  
                  {/* Entity links if present */}
                  {insight.entity_type === 'deal' && (
                    <div className="mb-3">
                      <Link to="/pipeline" className="text-sm font-medium text-brand-600 hover:underline">
                        View Deal #{insight.entity_id}
                      </Link>
                    </div>
                  )}
                  {insight.entity_type === 'customer' && (
                    <div className="mb-3">
                      <Link to={`/customers/${insight.entity_id}/360`} className="text-sm font-medium text-brand-600 hover:underline">
                        View Customer #{insight.entity_id}
                      </Link>
                    </div>
                  )}

                  <p className="text-sm text-gray-600 mb-4 leading-relaxed">
                    {insight.description}
                  </p>

                  <div className="bg-brand-50 border border-brand-100 rounded-lg p-3">
                    <div className="text-xs font-semibold text-brand-800 mb-1">Recommended:</div>
                    <div className="text-sm text-brand-900">{insight.recommendation}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Connected Stat Cards */}
        <div className="flex mb-10 rounded-lg shadow-sm gap-4">
          <div className="flex-1">
            <StatCard title="Unified Profiles" value={unifiedProfilesCount.toString()} subtext="Total customers" />
          </div>
          <div className="flex-1">
            <StatCard title="Pipeline Value" value={`$${totalDealValue.toFixed(2)}`} subtext={`${deals.length} active deals`} isPositive={true} />
          </div>
          <div className="flex-1">
            <StatCard title="Won Revenue" value={`$${wonRevenue.toFixed(2)}`} subtext="Closed won deals" isPositive={true} />
          </div>
          <div className="flex-1">
            <StatCard title="System Health" value="100%" subtext="All systems operational" isPositive={true} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-8 mb-8">
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Events</h3>
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
                    <span className={`px-2 py-1 text-xs rounded ${ev.processed ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                      {ev.processed ? 'Processed' : 'Pending'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold mb-4">Workflow Executions</h3>
            {executions.length === 0 ? (
              <div className="text-gray-500 text-sm">No recent executions found.</div>
            ) : (
              <div className="space-y-3">
                {executions.map((ex: any) => (
                  <div key={ex.id} className="text-sm flex justify-between items-center border-b border-gray-100 pb-2">
                    <div>
                      <span className="font-medium">{ex.workflow_name}</span>
                      <div className="text-xs text-gray-500 mt-1">Event: {ex.raw_event}</div>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded ${
                      ex.status === 'success' ? 'bg-green-100 text-green-700' : 
                      ex.status === 'skipped' ? 'bg-gray-100 text-gray-700' : 
                      'bg-red-100 text-red-700'
                    }`}>
                      {ex.status.toUpperCase()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div>
          <CustomerTable customers={customers} />
        </div>
      </div>
    </div>
  );
};
