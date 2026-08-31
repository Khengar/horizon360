import React, { useEffect, useState } from 'react';
import { StatCard } from '../components/StatCard';
import { CustomerTable } from '../components/CustomerTable';
import { horizonApi } from '../api';
import { Link } from 'react-router-dom';
import { Copilot } from '../components/Copilot';

export const Dashboard = () => {
  const [customers, setCustomers] = useState<any[]>([]);
  const [deals, setDeals] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [executions, setExecutions] = useState<any[]>([]);
  const [insights, setInsights] = useState([]);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [tickets, setTickets] = useState<any[]>([]);
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [leads, setLeads] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [runningMesh, setRunningMesh] = useState(false);
  const [meshStatus, setMeshStatus] = useState<string | null>(null);
  const [selectedAgentFilter, setSelectedAgentFilter] = useState<string>('all');
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  
  const loadDashboardData = (agentFilter = 'all') => {
    horizonApi.getCustomers().then(data => setCustomers(data)).catch(console.error);
    horizonApi.getDeals().then(data => setDeals(data)).catch(console.error);
    horizonApi.getEvents().then(data => setEvents(data.slice(0, 10))).catch(console.error);
    horizonApi.getWorkflowExecutions().then(data => setExecutions(data.slice(0, 10))).catch(console.error);
    horizonApi.getInvoices().then(data => setInvoices(data)).catch(console.error);
    horizonApi.getServiceTickets().then(data => setTickets(data)).catch(console.error);
    horizonApi.getCampaigns().then(data => setCampaigns(data)).catch(console.error);
    horizonApi.getLeads().then(data => setLeads(data)).catch(console.error);
    horizonApi.getProjects().then(data => setProjects(data)).catch(console.error);
    
    const params = agentFilter !== 'all' ? { agent_type: agentFilter } : undefined;
    horizonApi.getInsights(params).then(data => setInsights(data)).catch(console.error);
  };

  useEffect(() => {
    loadDashboardData(selectedAgentFilter);
  }, [selectedAgentFilter]);

  const handleRunMesh = async () => {
    setRunningMesh(true);
    setMeshStatus(null);
    try {
      const res = await horizonApi.runIntelligenceMesh();
      const summaries = res.agent_summaries ? Object.entries(res.agent_summaries).map(([k, v]) => `${k}: ${v}`).join(', ') : '';
      setMeshStatus(`✓ Federated Mesh executed across ${res.agents_executed} agents (${summaries}). Total insights generated: ${res.total_insights_generated}.`);
      loadDashboardData(selectedAgentFilter);
    } catch (err) {
      setMeshStatus('Failed to run Intelligence Mesh.');
    } finally {
      setRunningMesh(false);
    }
  };

  const handleExecuteAction = async (insight: any, actionType: string) => {
    try {
      const res = await horizonApi.executeAction({
        action_type: actionType,
        entity_type: insight.entity_type,
        entity_id: insight.entity_id,
        insight_id: insight.id,
        payload: { tag: `AI_${insight.agent_type.toUpperCase()}_ACTIONED` }
      });
      setActionMessage(`✓ Action executed: ${res.message}`);
      setTimeout(() => setActionMessage(null), 5000);
      loadDashboardData(selectedAgentFilter);
    } catch (err) {
      setActionMessage('Failed to execute action.');
      setTimeout(() => setActionMessage(null), 4000);
    }
  };

  const unifiedProfilesCount = customers.length;
  const totalDealValue = deals.reduce((sum, d: any) => sum + parseFloat(d.value || 0), 0);
  const wonRevenue = deals.filter((d: any) => d.stage === 'won').reduce((sum, d: any) => sum + parseFloat(d.value || 0), 0);

  const agentFilters = [
    { id: 'all', label: 'All Agents' },
    { id: 'sales', label: 'Sales' },
    { id: 'customer_success', label: 'Customer Success' },
    { id: 'marketing', label: 'Marketing' },
    { id: 'service', label: 'Service' },
    { id: 'finance', label: 'Finance' },
    { id: 'executive', label: 'Executive' }
  ];

  return (
    <div className="flex-1 flex flex-col h-full bg-white overflow-y-auto">
      {/* Top Header */}
      <header className="h-14 border-b border-gray-200 flex items-center px-8 justify-between shrink-0">
         <div className="flex items-center text-sm text-gray-500">
           <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span> Multi-Agent Mesh Active (6 Federated Agents)
         </div>
         <div className="flex items-center gap-4">
            <button
              onClick={handleRunMesh}
              disabled={runningMesh}
              className="bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold px-3.5 py-1.5 rounded-lg shadow-sm transition-colors flex items-center gap-1.5 disabled:opacity-50"
            >
              {runningMesh ? "Agents Running..." : "⚡ Run All 6 Agents"}
            </button>
            <input type="text" placeholder="Search resources..." className="bg-gray-100 text-sm rounded px-3 py-1.5 w-64 border-transparent focus:bg-white focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none" />
         </div>
      </header>

      {/* Main Content Area */}
      <div className="p-8 max-w-6xl w-full">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900">Unified Profiles & CRM</h2>
          <p className="text-gray-500 mt-1">Universal Business Operating System powered by Federated Multi-Agent Intelligence.</p>
        </div>
        
        <Copilot />

        {/* Intelligence Center */}
        <div className="mb-10">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                Intelligence Center
                <span className="text-xs bg-purple-100 text-purple-800 font-semibold px-2.5 py-0.5 rounded-full">
                  {insights.length} Active Insights
                </span>
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">Real-time alerts generated across Sales, Customer Success, Marketing, Service, Finance, and Executive BIOMs.</p>
            </div>
            <button 
              onClick={handleRunMesh}
              disabled={runningMesh}
              className="text-xs font-semibold text-brand-600 hover:text-brand-800 underline"
            >
              {runningMesh ? "Scanning UDM..." : "Re-scan Signals"}
            </button>
          </div>

          {/* Agent Type Filter Pills */}
          <div className="flex flex-wrap gap-2 mb-4">
            {agentFilters.map(af => (
              <button
                key={af.id}
                onClick={() => setSelectedAgentFilter(af.id)}
                className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors ${
                  selectedAgentFilter === af.id
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {af.label}
              </button>
            ))}
          </div>

          {meshStatus && (
            <div className="mb-4 text-xs bg-brand-50 border border-brand-200 text-brand-800 px-4 py-2.5 rounded-lg">
              {meshStatus}
            </div>
          )}

          {actionMessage && (
            <div className="mb-4 text-xs bg-green-50 border border-green-200 text-green-800 px-4 py-2.5 rounded-lg">
              {actionMessage}
            </div>
          )}

          {insights.length === 0 ? (
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center text-gray-500 text-sm">
              No insights found for this filter. Click <strong>"Run All 6 Agents"</strong> to evaluate the entire Universal Data Model.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {insights.map((insight: any) => (
                <div key={insight.id} className="bg-white border border-gray-200 rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-start mb-3">
                      <span className={`px-2 py-1 text-xs font-semibold rounded ${
                        insight.severity === 'critical' ? 'bg-red-100 text-red-700' :
                        insight.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                        insight.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {insight.severity.toUpperCase()} RISK
                      </span>
                      <span className="text-xs text-gray-400 capitalize bg-gray-100 px-2 py-0.5 rounded font-mono">
                        {insight.agent_type.replace('_', ' ')}
                      </span>
                    </div>
                    
                    <h4 className="font-bold text-gray-900 mb-1">{insight.title}</h4>
                    
                    {/* Entity links if present */}
                    {insight.entity_type === 'deal' && (
                      <div className="mb-2">
                        <Link to="/pipeline" className="text-xs font-medium text-brand-600 hover:underline">
                          View Deal #{insight.entity_id}
                        </Link>
                      </div>
                    )}
                    {insight.entity_type === 'customer' && (
                      <div className="mb-2">
                        <Link to={`/customers/${insight.entity_id}/360`} className="text-xs font-medium text-brand-600 hover:underline">
                          View Customer 360
                        </Link>
                      </div>
                    )}

                    <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                      {insight.description}
                    </p>
                  </div>

                  <div>
                    <div className="bg-brand-50 border border-brand-100 rounded-lg p-3 mb-3">
                      <div className="text-xs font-semibold text-brand-800 mb-1">AI Recommendation:</div>
                      <div className="text-xs text-brand-900">{insight.recommendation}</div>
                    </div>

                    {/* Action Execution Buttons */}
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleExecuteAction(insight, 'apply_tag')}
                        className="flex-1 text-xs bg-brand-600 hover:bg-brand-700 text-white font-medium py-1.5 px-2 rounded-lg shadow-sm transition-colors text-center"
                      >
                        ⚡ Apply AI Playbook
                      </button>
                      {insight.entity_type === 'customer' && (
                        <button
                          onClick={() => handleExecuteAction(insight, 'draft_email')}
                          className="text-xs bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 font-medium py-1.5 px-2 rounded-lg transition-colors"
                        >
                          Draft Email
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Cross-BIOM Overview */}
        <div className="mb-10">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Cross-BIOM Overview</h3>
          <div className="grid grid-cols-5 gap-4">
            {/* Sales */}
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Sales</h4>
              <div className="space-y-3">
                <div>
                  <div className="text-[10px] text-gray-500">Pipeline</div>
                  <div className="font-bold text-gray-900">${deals.filter(d => d.stage !== 'won' && d.stage !== 'lost').reduce((s,d)=>s+parseFloat(d.value||0),0).toFixed(0)}</div>
                </div>
                <div>
                  <div className="text-[10px] text-gray-500">Won Revenue</div>
                  <div className="font-bold text-green-600">${deals.filter(d => d.stage === 'won').reduce((s,d)=>s+parseFloat(d.value||0),0).toFixed(0)}</div>
                </div>
              </div>
            </div>

            {/* Finance */}
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Finance</h4>
              <div className="space-y-3">
                <div>
                  <div className="text-[10px] text-gray-500">Invoices</div>
                  <div className="font-bold text-gray-900">{invoices.length}</div>
                </div>
                <div>
                  <div className="text-[10px] text-gray-500">Outstanding</div>
                  <div className="font-bold text-orange-600">${invoices.filter((i:any) => ['draft', 'requested', 'issued', 'overdue'].includes(i.status)).reduce((s:any, i:any) => s + parseFloat(i.amount||0), 0).toFixed(0)}</div>
                </div>
                <div>
                  <div className="text-[10px] text-gray-500">Paid</div>
                  <div className="font-bold text-green-600">${invoices.filter((i:any) => i.status === 'paid').reduce((s:any, i:any) => s + parseFloat(i.amount||0), 0).toFixed(0)}</div>
                </div>
              </div>
            </div>

            {/* Service */}
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Service</h4>
              <div className="space-y-3">
                <div>
                  <div className="text-[10px] text-gray-500">Open Tickets</div>
                  <div className="font-bold text-gray-900">{tickets.filter((t:any) => t.status === 'open' || t.status === 'in_progress').length}</div>
                </div>
                <div>
                  <div className="text-[10px] text-gray-500">Critical Tickets</div>
                  <div className="font-bold text-red-600">{tickets.filter((t:any) => t.priority === 'critical' && t.status !== 'resolved' && t.status !== 'closed').length}</div>
                </div>
              </div>
            </div>

            {/* Marketing */}
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Marketing</h4>
              <div className="space-y-3">
                <div>
                  <div className="text-[10px] text-gray-500">Active Campaigns</div>
                  <div className="font-bold text-gray-900">{campaigns.filter((c:any) => c.status === 'active').length}</div>
                </div>
                <div>
                  <div className="text-[10px] text-gray-500">Qualified Leads</div>
                  <div className="font-bold text-blue-600">{leads.filter((l:any) => l.status === 'qualified' || l.status === 'converted').length}</div>
                </div>
              </div>
            </div>

            {/* Projects */}
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Projects</h4>
              <div className="space-y-3">
                <div>
                  <div className="text-[10px] text-gray-500">Active Projects</div>
                  <div className="font-bold text-gray-900">{projects.filter((p:any) => p.status === 'active').length}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-8 mb-8">
          {/* Cross-BIOM Activity */}
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold mb-4">Cross-BIOM Activity</h3>
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
          
          {/* Horizon Flow */}
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold mb-4">Horizon Flow</h3>
            {executions.length === 0 ? (
              <div className="text-gray-500 text-sm">No recent executions found.</div>
            ) : (
              <div className="relative pl-4 space-y-6 before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-300 before:to-transparent">
                {executions.map((ex: any) => (
                  <div key={ex.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    <div className="flex items-center justify-center w-6 h-6 rounded-full border border-white bg-brand-500 text-slate-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                      <div className="w-2 h-2 bg-white rounded-full"></div>
                    </div>
                    <div className="w-[calc(100%-2.5rem)] md:w-[calc(50%-1.5rem)] p-3 rounded-lg border border-gray-200 bg-white shadow-sm">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-bold text-sm text-gray-900">{ex.workflow_name}</span>
                        <span className={`px-2 py-0.5 text-[10px] uppercase font-bold rounded ${
                          ex.status === 'success' ? 'bg-green-100 text-green-700' : 
                          ex.status === 'skipped' ? 'bg-gray-100 text-gray-700' : 
                          'bg-red-100 text-red-700'
                        }`}>
                          {ex.status}
                        </span>
                      </div>
                      <div className="text-xs text-brand-600 font-mono mb-1">Trigger: {ex.trigger_event}</div>
                      <div className="text-[10px] text-gray-500">{new Date(ex.created_at).toLocaleString()}</div>
                    </div>
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
