import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';
import { Target as TargetIcon, TrendingUp, AlertTriangle, Plus, X, Search, ChevronLeft, ChevronRight, Calendar } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

export const Projects = () => {
  const [targets, setTargets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTarget, setNewTarget] = useState({
    title: '',
    metric_type: 'revenue',
    target_amount: '',
    start_date: new Date().toISOString().split('T')[0],
    deadline: ''
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setLoading(true);
    horizonApi.getTargets(page).then((data) => {
      setTargets(data.results || []);
      setTotalPages(Math.ceil((data.count || 0) / 10));
      setLoading(false);
    }).catch(console.error);
  }, [page]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      // Ensure date formats
      const payload = {
          ...newTarget,
          start_date: new Date(newTarget.start_date).toISOString(),
          deadline: new Date(newTarget.deadline).toISOString()
      };
      await horizonApi.createTarget(payload);
      const updated = await horizonApi.getTargets(page);
      setTargets(updated.results || []);
      setTotalPages(Math.ceil((updated.count || 0) / 10));
      setIsModalOpen(false);
      setNewTarget({ title: '', metric_type: 'revenue', target_amount: '', start_date: new Date().toISOString().split('T')[0], deadline: '' });
    } catch (err) {
      console.error(err);
      alert('Failed to save target. Check console.');
    } finally {
      setSubmitting(false);
    }
  };

  const filteredTargets = targets.filter(t => 
    t.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Chart Data preparation
  const chartData = filteredTargets.map(t => ({
    name: t.title.substring(0, 15) + (t.title.length > 15 ? '...' : ''),
    target: parseFloat(t.target_amount),
    progress: t.current_progress,
    type: t.metric_type
  }));

  const overallRevenueTarget = targets.filter(t => t.metric_type === 'revenue').reduce((s, t) => s + parseFloat(t.target_amount), 0);
  const overallRevenueProgress = targets.filter(t => t.metric_type === 'revenue').reduce((s, t) => s + t.current_progress, 0);
  
  const overallExpenseTarget = targets.filter(t => t.metric_type === 'expense').reduce((s, t) => s + parseFloat(t.target_amount), 0);
  const overallExpenseProgress = targets.filter(t => t.metric_type === 'expense').reduce((s, t) => s + t.current_progress, 0);

  return (
    <div className="flex-1 p-8 bg-gray-50 h-full overflow-y-auto">
      <div className="max-w-6xl w-full mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-3xl font-bold text-gray-900">Targets & Goals (Master Analysis)</h2>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-700 transition-colors">
            <Plus className="w-4 h-4" /> New Target
          </button>
        </div>

        {/* Master Analysis KPI Cards */}
        <div className="grid grid-cols-2 gap-4 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-500 flex items-center gap-2"><TrendingUp className="w-4 h-4 text-green-600"/> Global Revenue Targets</h3>
                <p className="text-3xl font-bold mt-2 text-gray-900">${overallRevenueProgress.toFixed(2)} <span className="text-lg text-gray-400 font-normal">/ ${overallRevenueTarget.toFixed(2)}</span></p>
              </div>
              {overallRevenueTarget > 0 && (
                <div className="text-right">
                  <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-green-100 text-green-700 font-bold text-sm">
                    {((overallRevenueProgress / overallRevenueTarget) * 100).toFixed(0)}%
                  </div>
                </div>
              )}
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-4">
              <div className="bg-green-500 h-2 rounded-full" style={{ width: `${Math.min((overallRevenueProgress / (overallRevenueTarget || 1)) * 100, 100)}%` }}></div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-500 flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-red-600"/> Global Expense Limits</h3>
                <p className="text-3xl font-bold mt-2 text-gray-900">${overallExpenseProgress.toFixed(2)} <span className="text-lg text-gray-400 font-normal">/ ${overallExpenseTarget.toFixed(2)}</span></p>
              </div>
              {overallExpenseTarget > 0 && (
                <div className="text-right">
                  <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-red-100 text-red-700 font-bold text-sm">
                    {((overallExpenseProgress / overallExpenseTarget) * 100).toFixed(0)}%
                  </div>
                </div>
              )}
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-4">
              <div className={`h-2 rounded-full ${overallExpenseProgress > overallExpenseTarget ? 'bg-red-600' : 'bg-orange-400'}`} style={{ width: `${Math.min((overallExpenseProgress / (overallExpenseTarget || 1)) * 100, 100)}%` }}></div>
            </div>
          </div>
        </div>

        {/* Master Chart */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8">
          <h3 className="text-lg font-semibold mb-6 text-gray-800">Target Progress vs Goal</h3>
          {chartData.length > 0 ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                  <XAxis dataKey="name" tick={{fontSize: 12, fill: '#6b7280'}} axisLine={false} tickLine={false} />
                  <YAxis tick={{fontSize: 12, fill: '#6b7280'}} axisLine={false} tickLine={false} tickFormatter={(value) => `$${value}`} />
                  <Tooltip cursor={{fill: '#f3f4f6'}} formatter={(value) => [`$${parseFloat(value as string).toFixed(2)}`, '']} />
                  <Legend wrapperStyle={{fontSize: '12px', paddingTop: '10px'}} />
                  <Bar dataKey="progress" name="Current Progress" fill="#0ea5e9" radius={[4, 4, 0, 0]} maxBarSize={60} />
                  <Bar dataKey="target" name="Goal/Limit" fill="#e5e7eb" radius={[4, 4, 0, 0]} maxBarSize={60} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex h-40 items-center justify-center text-gray-400">
              No targets found. Create one to see the analysis.
            </div>
          )}
        </div>

        {/* Target Rows (List) */}
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
            <h3 className="text-lg font-semibold">Active Targets</h3>
            <div className="relative">
              <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search targets..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 w-64"
              />
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-white">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Goal Title</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timeline</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Progress</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/4">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-500">Loading targets...</td></tr>
                ) : filteredTargets.length === 0 ? (
                  <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-500">No targets found.</td></tr>
                ) : (
                  filteredTargets.map((t) => {
                    const progressPct = Math.min((t.current_progress / parseFloat(t.target_amount)) * 100, 100);
                    const isRevenue = t.metric_type === 'revenue';
                    
                    // Logic: for revenue, high progress is good (green). for expense, high progress is bad (red).
                    let barColor = isRevenue ? 'bg-green-500' : 'bg-orange-400';
                    if (!isRevenue && t.current_progress > parseFloat(t.target_amount)) barColor = 'bg-red-600';

                    return (
                      <tr key={t.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-bold text-gray-900">{t.title}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            isRevenue ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {isRevenue ? 'Revenue Goal' : 'Expense Limit'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <div className="flex items-center gap-1"><Calendar className="w-3 h-3"/> {new Date(t.start_date).toLocaleDateString()}</div>
                          <div className="flex items-center gap-1 text-gray-400 mt-1"><TargetIcon className="w-3 h-3"/> {new Date(t.deadline).toLocaleDateString()}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-right">
                          <div className="text-gray-900">${t.current_progress.toFixed(2)}</div>
                          <div className="text-gray-400 text-xs mt-0.5">/ ${parseFloat(t.target_amount).toFixed(2)}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-3">
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div className={`${barColor} h-2 rounded-full`} style={{ width: `${progressPct}%` }}></div>
                            </div>
                            <span className="text-xs font-bold text-gray-600 w-8">{progressPct.toFixed(0)}%</span>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <div className="px-6 py-3 border-t border-gray-200 flex items-center justify-between bg-gray-50">
            <span className="text-sm text-gray-700">
              Page <span className="font-medium">{page}</span> of <span className="font-medium">{totalPages || 1}</span>
            </span>
            <div className="flex gap-2">
              <button disabled={page === 1} onClick={() => setPage(p => Math.max(1, p - 1))} className="p-1 rounded bg-white border border-gray-300 disabled:opacity-50"><ChevronLeft className="w-5 h-5" /></button>
              <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)} className="p-1 rounded bg-white border border-gray-300 disabled:opacity-50"><ChevronRight className="w-5 h-5" /></button>
            </div>
          </div>
        </div>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-gray-900/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold">Set New Target</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Target Title</label>
                <input required type="text" value={newTarget.title} onChange={e => setNewTarget({...newTarget, title: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" placeholder="e.g. Q4 Revenue Push" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Target Type</label>
                <select required value={newTarget.metric_type} onChange={e => setNewTarget({...newTarget, metric_type: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                  <option value="revenue">Revenue Goal (Money Made)</option>
                  <option value="expense">Expense Limit (Money Spent)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Target Amount ($)</label>
                <input required type="number" step="0.01" value={newTarget.target_amount} onChange={e => setNewTarget({...newTarget, target_amount: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" placeholder="50000.00" />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                  <input required type="date" value={newTarget.start_date} onChange={e => setNewTarget({...newTarget, start_date: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Deadline</label>
                  <input required type="date" value={newTarget.deadline} onChange={e => setNewTarget({...newTarget, deadline: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
                </div>
              </div>

              <div className="pt-4 flex justify-end gap-3">
                <button type="button" onClick={() => setIsModalOpen(false)} className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg">Cancel</button>
                <button type="submit" disabled={submitting} className="px-4 py-2 text-sm text-white bg-brand-600 hover:bg-brand-700 rounded-lg disabled:opacity-50">
                  {submitting ? 'Saving...' : 'Set Target'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
