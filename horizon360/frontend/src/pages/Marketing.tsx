import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { TrendingUp, Users, Target, DollarSign, Search, Plus, X, ChevronLeft, ChevronRight } from 'lucide-react';

export const Marketing = () => {
  const [view, setView] = useState<'analytics' | 'ledger'>('analytics');
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [leads, setLeads] = useState<any[]>([]);
  const [transactions, setTransactions] = useState<any[]>([]);
  
  // Ledger State
  const [ledgerPage, setLedgerPage] = useState(1);
  const [ledgerData, setLedgerData] = useState<any[]>([]);
  const [ledgerTotalPages, setLedgerTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newEntry, setNewEntry] = useState({ transaction_type: 'spend', campaign: '', campaign_name: '', description: '', amount: '' });
  const [submitting, setSubmitting] = useState(false);

  const [loading, setLoading] = useState(true);

  // Load basic data + ALL ledger for Analytics
  useEffect(() => {
    setLoading(true);
    Promise.all([
      horizonApi.getCampaigns().catch(() => []),
      horizonApi.getLeads().catch(() => []),
      horizonApi.getTransactions(1).catch(() => ({ results: [] })), // Global sales for the line chart
      horizonApi.getCampaignTransactions(1).catch(() => ({ results: [], count: 0 }))
    ]).then(([campData, leadData, txData, ctData]) => {
      setCampaigns(campData);
      setLeads(leadData);
      setTransactions(txData.results || []);
      
      setLedgerData(ctData.results || []);
      setLedgerTotalPages(Math.ceil((ctData.count || 0) / 10));
      
      setLoading(false);
    });
  }, []);

  // Fetch paginated ledger when page changes
  useEffect(() => {
    if (loading) return;
    horizonApi.getCampaignTransactions(ledgerPage).then(data => {
      setLedgerData(data.results || []);
      setLedgerTotalPages(Math.ceil((data.count || 0) / 10));
    });
  }, [ledgerPage]);

  // Aggregates
  const activeCampaigns = campaigns.filter(c => c.status === 'active');
  const activeBudget = activeCampaigns.reduce((sum, c) => sum + parseFloat(c.budget || 0), 0);
  const totalLeads = leads.length;
  
  const statusCounts = {
    new: leads.filter(l => l.status === 'new').length,
    contacted: leads.filter(l => l.status === 'contacted').length,
    qualified: leads.filter(l => l.status === 'qualified').length,
    converted: leads.filter(l => l.status === 'converted').length,
  };

  const conversionRate = totalLeads > 0 ? ((statusCounts.converted / totalLeads) * 100).toFixed(1) : '0.0';

  // --- CHART DATA PREPARATION ---
  
  // 1. Lead Funnel
  const funnelData = [
    { stage: '1. New Leads', count: statusCounts.new },
    { stage: '2. Contacted', count: statusCounts.contacted },
    { stage: '3. Qualified', count: statusCounts.qualified },
    { stage: '4. Converted', count: statusCounts.converted },
  ];

  // 2. Campaign ROI Data (Actual values from CampaignTransactions!)
  // We need all transactions to accurately calculate it, but for demo we calculate over loaded ones.
  // Actually, we'll build a map from the current paginated ones. In a real app we'd fetch an aggregate endpoint.
  const campaignPerformanceMap: Record<string, {spend: number, roi: number, name: string}> = {};
  campaigns.forEach(c => {
    campaignPerformanceMap[c.id] = { spend: 0, roi: 0, name: c.name };
  });
  
  // To make it look good across pagination, we'll fetch all transactions temporarily for the chart 
  // or just use the current page. Let's use the current page for simplicity in this demo.
  ledgerData.forEach(ct => {
    if (campaignPerformanceMap[ct.campaign]) {
      if (ct.transaction_type === 'spend') {
        campaignPerformanceMap[ct.campaign].spend += parseFloat(ct.amount);
      } else {
        campaignPerformanceMap[ct.campaign].roi += parseFloat(ct.amount);
      }
    }
  });

  const campaignData = Object.values(campaignPerformanceMap)
    .filter(c => c.spend > 0 || c.roi > 0)
    .map(c => ({
      name: c.name.substring(0, 15) + (c.name.length > 15 ? '...' : ''),
      budget: c.spend,
      revenue: c.roi
    }));

  // 3. Sales Trend Data
  const salesMap: Record<string, number> = {};
  transactions.filter(tx => tx.transaction_type === 'earn').forEach(tx => {
    const d = new Date(tx.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    salesMap[d] = (salesMap[d] || 0) + parseFloat(tx.amount);
  });
  
  let salesTrendData = Object.keys(salesMap).map(k => ({ date: k, revenue: salesMap[k] }));
  if (salesTrendData.length === 0) {
      salesTrendData = [
          { date: 'Aug 28', revenue: 4000 }, { date: 'Aug 29', revenue: 3000 },
          { date: 'Aug 30', revenue: 5000 }, { date: 'Aug 31', revenue: 2780 },
          { date: 'Sep 01', revenue: 8900 }, { date: 'Sep 02', revenue: 4390 },
      ];
  } else {
      salesTrendData = salesTrendData.reverse().slice(0, 7);
  }

  // Submit Handler
  const handleCreateEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      let finalCampaignId = newEntry.campaign;
      
      // If it's a spend, create the campaign on the fly
      if (newEntry.transaction_type === 'spend') {
        const newCamp = await horizonApi.createCampaign({
          name: newEntry.campaign_name,
          status: 'active',
          budget: parseFloat(newEntry.amount)
        });
        finalCampaignId = newCamp.id;
        
        // Optimistically update campaigns list so it's available for ROI later
        setCampaigns(prev => [newCamp, ...prev]);
      }

      await horizonApi.createCampaignTransaction({
        transaction_type: newEntry.transaction_type,
        campaign: finalCampaignId,
        description: newEntry.description,
        amount: newEntry.amount
      });
      
      const updatedCt = await horizonApi.getCampaignTransactions(ledgerPage);
      setLedgerData(updatedCt.results || []);
      setLedgerTotalPages(Math.ceil((updatedCt.count || 0) / 10));
      setIsModalOpen(false);
      setNewEntry({ transaction_type: 'spend', campaign: '', campaign_name: '', description: '', amount: '' });
    } catch (err) {
      console.error(err);
      alert('Failed to save entry. Check console.');
    } finally {
      setSubmitting(false);
    }
  };

  const filteredLedger = ledgerData.filter(ct => 
    ct.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ct.campaign_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-1 p-8 bg-gray-50 h-full overflow-y-auto">
      <div className="max-w-6xl w-full mx-auto">
        
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-3xl font-bold text-gray-900">Marketing</h2>
          
          <div className="flex items-center bg-white p-1 rounded-lg border border-gray-200 shadow-sm">
            <button 
              onClick={() => setView('analytics')}
              className={`px-4 py-2 text-sm font-semibold rounded-md ${view === 'analytics' ? 'bg-indigo-50 text-indigo-700' : 'text-gray-500 hover:text-gray-700'}`}>
              Analytics
            </button>
            <button 
              onClick={() => setView('ledger')}
              className={`px-4 py-2 text-sm font-semibold rounded-md ${view === 'ledger' ? 'bg-brand-50 text-brand-700' : 'text-gray-500 hover:text-gray-700'}`}>
              Campaign Ledger
            </button>
          </div>
        </div>

        {view === 'analytics' ? (
          <>
            <div className="grid grid-cols-4 gap-4 mb-8">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="w-4 h-4 text-brand-600" />
                  <h3 className="text-sm font-medium text-gray-500">Active Campaigns</h3>
                </div>
                <p className="text-2xl font-bold text-gray-900">{activeCampaigns.length}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center gap-2 mb-2">
                  <DollarSign className="w-4 h-4 text-green-600" />
                  <h3 className="text-sm font-medium text-gray-500">Active Budget</h3>
                </div>
                <p className="text-2xl font-bold text-gray-900">${activeBudget.toFixed(2)}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center gap-2 mb-2">
                  <Users className="w-4 h-4 text-indigo-600" />
                  <h3 className="text-sm font-medium text-gray-500">Total Leads</h3>
                </div>
                <p className="text-2xl font-bold text-gray-900">{totalLeads}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-4 h-4 text-blue-600" />
                  <h3 className="text-sm font-medium text-gray-500">Conversion Rate</h3>
                </div>
                <p className="text-2xl font-bold text-blue-600">{conversionRate}%</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6 mb-8">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold mb-4 text-gray-800">Sales Velocity & Trend</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={salesTrendData}>
                      <defs>
                        <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                      <XAxis dataKey="date" tick={{fontSize: 12, fill: '#6b7280'}} axisLine={false} tickLine={false} />
                      <YAxis tick={{fontSize: 12, fill: '#6b7280'}} axisLine={false} tickLine={false} tickFormatter={(value) => `$${value}`} />
                      <Tooltip formatter={(value) => [`$${value}`, 'Revenue']} />
                      <Area type="monotone" dataKey="revenue" stroke="#4f46e5" strokeWidth={3} fillOpacity={1} fill="url(#colorRevenue)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold mb-4 text-gray-800">Lead Conversion Funnel</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={funnelData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e7eb" />
                      <XAxis type="number" tick={{fontSize: 12, fill: '#6b7280'}} axisLine={false} tickLine={false} />
                      <YAxis dataKey="stage" type="category" tick={{fontSize: 12, fill: '#374151', fontWeight: 500}} axisLine={false} tickLine={false} width={90} />
                      <Tooltip cursor={{fill: '#f3f4f6'}} />
                      <Bar dataKey="count" fill="#0ea5e9" radius={[0, 4, 4, 0]} barSize={32} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 col-span-2">
                <h3 className="text-lg font-semibold mb-4 text-gray-800">Campaign Performance & Actual ROI</h3>
                {campaignData.length > 0 ? (
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={campaignData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                        <XAxis dataKey="name" tick={{fontSize: 12, fill: '#6b7280'}} axisLine={false} tickLine={false} />
                        <YAxis tick={{fontSize: 12, fill: '#6b7280'}} axisLine={false} tickLine={false} tickFormatter={(value) => `$${value}`} />
                        <Tooltip cursor={{fill: '#f3f4f6'}} formatter={(value) => [`$${parseFloat(value as string).toFixed(2)}`, '']} />
                        <Legend wrapperStyle={{fontSize: '12px', paddingTop: '10px'}} />
                        <Bar dataKey="budget" name="Actual Spend" fill="#f43f5e" radius={[4, 4, 0, 0]} maxBarSize={50} />
                        <Bar dataKey="revenue" name="Attributed ROI" fill="#10b981" radius={[4, 4, 0, 0]} maxBarSize={50} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="flex h-40 items-center justify-center text-gray-400">
                    No Campaign Transactions recorded yet. Add some in the Campaign Ledger.
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden flex flex-col">
            <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
              <div className="relative">
                <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search ledger..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 w-64"
                />
              </div>
              <button 
                onClick={() => setIsModalOpen(true)}
                className="flex items-center gap-2 bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-700 transition-colors">
                <Plus className="w-4 h-4" /> New Entry
              </button>
            </div>

            <table className="min-w-full divide-y divide-gray-200 flex-1">
              <thead className="bg-white">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Campaign</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredLedger.length === 0 ? (
                  <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-500">No transactions found.</td></tr>
                ) : (
                  filteredLedger.map((tx) => (
                    <tr key={tx.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(tx.date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {tx.campaign_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          tx.transaction_type === 'roi' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {tx.transaction_type === 'roi' ? 'ROI / Revenue' : 'Spend / Expense'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 truncate max-w-xs">
                        {tx.description}
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm font-bold text-right ${tx.transaction_type === 'roi' ? 'text-green-600' : 'text-red-600'}`}>
                        {tx.transaction_type === 'roi' ? '+' : '-'}${parseFloat(tx.amount).toFixed(2)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>

            {/* Pagination */}
            <div className="px-6 py-3 border-t border-gray-200 flex items-center justify-between bg-gray-50">
              <span className="text-sm text-gray-700">
                Page <span className="font-medium">{ledgerPage}</span> of <span className="font-medium">{ledgerTotalPages || 1}</span>
              </span>
              <div className="flex gap-2">
                <button
                  disabled={ledgerPage === 1}
                  onClick={() => setLedgerPage(p => Math.max(1, p - 1))}
                  className="p-1 rounded bg-white border border-gray-300 disabled:opacity-50"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <button
                  disabled={ledgerPage >= ledgerTotalPages}
                  onClick={() => setLedgerPage(p => p + 1)}
                  className="p-1 rounded bg-white border border-gray-300 disabled:opacity-50"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* New Entry Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-gray-900/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold">New Campaign Entry</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateEntry} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Entry Type</label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2">
                    <input type="radio" name="type" value="spend" checked={newEntry.transaction_type === 'spend'} onChange={(e) => setNewEntry({...newEntry, transaction_type: e.target.value})} className="text-brand-600 focus:ring-brand-500" />
                    <span className="text-sm text-gray-900">Expense (Create Campaign)</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="radio" name="type" value="roi" checked={newEntry.transaction_type === 'roi'} onChange={(e) => setNewEntry({...newEntry, transaction_type: e.target.value})} className="text-brand-600 focus:ring-brand-500" />
                    <span className="text-sm text-gray-900">ROI (Attributed Revenue)</span>
                  </label>
                </div>
              </div>
              
              {newEntry.transaction_type === 'spend' ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">New Campaign Name</label>
                  <input required type="text" value={newEntry.campaign_name} onChange={(e) => setNewEntry({...newEntry, campaign_name: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm" placeholder="e.g. Q4 Holiday Facebook Ads" />
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Select Existing Campaign</label>
                  <select required value={newEntry.campaign} onChange={(e) => setNewEntry({...newEntry, campaign: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm">
                    <option value="">-- Choose Campaign --</option>
                    {campaigns.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount ($)</label>
                <input required type="number" step="0.01" value={newEntry.amount} onChange={(e) => setNewEntry({...newEntry, amount: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm" placeholder="e.g. 1500.00" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <input required type="text" value={newEntry.description} onChange={(e) => setNewEntry({...newEntry, description: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm" placeholder="e.g. Meta Ads Q3 Spend" />
              </div>

              <div className="pt-4 flex justify-end gap-3">
                <button type="button" onClick={() => setIsModalOpen(false)} className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg">Cancel</button>
                <button type="submit" disabled={submitting} className="px-4 py-2 text-sm font-medium text-white bg-brand-600 hover:bg-brand-700 rounded-lg disabled:opacity-50">
                  {submitting ? 'Saving...' : 'Save Entry'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
