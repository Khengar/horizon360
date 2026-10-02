import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { Activity, Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

export const FlowAnalytics = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const data = await horizonApi.getV2FlowAnalytics();
        setMetrics(data);
      } catch (e) {
        console.error('Failed to load analytics', e);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAnalytics();
  }, []);

  if (loading) {
    return <div className="p-8 text-gray-500">Loading Analytics...</div>;
  }
  
  if (!metrics) {
    return <div className="p-8 text-red-500">Failed to load analytics dashboard.</div>;
  }

  // Format Recharts data (reverse so oldest is first, if backend didn't already sort it ascending. The backend sends 6 days ago -> today, so it's already chronological)
  const lineChartData = metrics.executions_over_time || [];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Analytics & SLA Dashboard</h2>
        <p className="text-gray-500 mt-1">Real-time metrics for Flow Engine executions and compliance</p>
      </div>

      {/* Top Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6 border border-gray-100 flex items-center">
          <div className="bg-blue-100 p-3 rounded-full text-blue-600 mr-4">
            <Activity size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">Total Runs</p>
            <p className="text-3xl font-bold text-gray-900">{metrics.total_executions}</p>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6 border border-gray-100 flex items-center">
          <div className="bg-green-100 p-3 rounded-full text-green-600 mr-4">
            <CheckCircle size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">Success Rate</p>
            <p className="text-3xl font-bold text-green-600">{metrics.success_rate}%</p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border border-gray-100 flex items-center">
          <div className="bg-red-100 p-3 rounded-full text-red-600 mr-4">
            <XCircle size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">Failure Rate</p>
            <p className="text-3xl font-bold text-red-600">{metrics.failure_rate}%</p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border border-gray-100 flex items-center">
          <div className="bg-indigo-100 p-3 rounded-full text-indigo-600 mr-4">
            <Clock size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">Avg Time</p>
            <p className="text-3xl font-bold text-gray-900">{metrics.avg_execution_seconds}s</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Charts Section */}
        <div className="lg:col-span-2 space-y-8">
          <div className="bg-white p-6 rounded-lg shadow border border-gray-100">
            <h3 className="text-lg font-bold text-gray-900 mb-6">Executions Over Time (7 Days)</h3>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={lineChartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="total" stroke="#6366f1" strokeWidth={3} dot={{r: 4}} name="Total Runs" />
                  <Line type="monotone" dataKey="success" stroke="#22c55e" strokeWidth={2} name="Successful" />
                  <Line type="monotone" dataKey="failed" stroke="#ef4444" strokeWidth={2} name="Failed" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow border border-gray-100">
            <h3 className="text-lg font-bold text-gray-900 mb-6">Execution Outcomes by Day</h3>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={lineChartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="success" stackId="a" fill="#22c55e" name="Success" />
                  <Bar dataKey="failed" stackId="a" fill="#ef4444" name="Failed" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* SLA Section */}
        <div className="bg-white p-6 rounded-lg shadow border border-gray-100 h-fit">
          <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center">
            <AlertTriangle className="mr-2 text-yellow-500" size={20} />
            SLA Compliance
          </h3>
          
          <div className="space-y-6">
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-gray-600">Total Monitored Tasks</span>
                <span className="font-bold">{metrics.sla_metrics.total_monitored}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full" style={{ width: '100%' }}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-gray-600">Tasks with Warnings</span>
                <span className="font-bold text-yellow-600">{metrics.sla_metrics.warnings}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-yellow-400 h-2 rounded-full" style={{ width: `${(metrics.sla_metrics.warnings / Math.max(metrics.sla_metrics.total_monitored, 1)) * 100}%` }}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-gray-600">SLA Breaches</span>
                <span className="font-bold text-red-600">{metrics.sla_metrics.breaches}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-red-500 h-2 rounded-full" style={{ width: `${(metrics.sla_metrics.breaches / Math.max(metrics.sla_metrics.total_monitored, 1)) * 100}%` }}></div>
              </div>
            </div>
          </div>

          <div className="mt-8 pt-6 border-t border-gray-100">
            <div className="text-center">
              <p className="text-5xl font-bold text-gray-900 mb-2">{metrics.sla_metrics.breach_rate}%</p>
              <p className="text-sm text-gray-500 uppercase tracking-widest font-medium">Global Breach Rate</p>
            </div>
            
            {metrics.sla_metrics.breach_rate > 5 && (
              <div className="mt-6 bg-red-50 text-red-700 p-4 rounded-md text-sm">
                <AlertTriangle className="inline mr-2 mb-1" size={16} />
                Breach rate is above the 5% threshold. Consider tuning SLA policies or provisioning more workers.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
