import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';
import { Network, ArrowRight, ArrowLeft, CheckCircle, XCircle, Activity, Globe } from 'lucide-react';

export const Integrations = () => {
  const [integrations, setIntegrations] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      horizonApi.getIntegrations(),
      horizonApi.getIntegrationLogs()
    ]).then(([integData, logsData]) => {
      setIntegrations(integData);
      setLogs(logsData);
      setLoading(false);
    }).catch(console.error);
  }, []);

  const inboundCount = logs.filter(l => l.direction === 'inbound').length;
  const outboundCount = logs.filter(l => l.direction === 'outbound').length;
  const failedCount = logs.filter(l => l.status === 'failed').length;

  return (
    <div className="flex-1 p-8 bg-slate-50 h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h2 className="text-3xl font-extrabold text-slate-900 flex items-center">
            <Network className="w-8 h-8 mr-3 text-indigo-600" />
            Horizon Nexus
          </h2>
          <p className="text-slate-600 mt-2 text-lg">Centralized integration gateway bridging Horizon 360 with external systems.</p>
        </div>

        {/* High-level stats */}
        <div className="grid grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Active Connections</h3>
            <p className="text-3xl font-black mt-2 text-slate-800">{integrations.filter(i => i.status === 'active').length}</p>
          </div>
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Inbound Events</h3>
            <p className="text-3xl font-black mt-2 text-green-600">{inboundCount}</p>
          </div>
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Outbound Events</h3>
            <p className="text-3xl font-black mt-2 text-blue-600">{outboundCount}</p>
          </div>
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Failed Events</h3>
            <p className="text-3xl font-black mt-2 text-red-600">{failedCount}</p>
          </div>
        </div>

        {/* Visual Architecture */}
        <div className="bg-indigo-900 rounded-xl p-8 mb-8 text-white shadow-lg overflow-hidden relative">
          <div className="absolute top-0 right-0 p-8 opacity-10">
            <Globe className="w-48 h-48" />
          </div>
          <h3 className="text-xl font-bold mb-6 flex items-center relative z-10">
            <Activity className="w-5 h-5 mr-2" />
            Integration Event Flow
          </h3>
          <div className="flex justify-between items-center relative z-10">
            {/* Inbound */}
            <div className="flex-1 text-center">
              <div className="text-indigo-200 text-sm font-bold mb-2 uppercase tracking-wide">External Systems</div>
              <div className="bg-indigo-800 border border-indigo-700 p-4 rounded-lg">Stripe, HubSpot, etc.</div>
            </div>
            
            <div className="px-6 flex flex-col items-center">
              <span className="text-xs text-green-400 font-bold mb-1">INBOUND</span>
              <ArrowRight className="text-green-400 w-8 h-8" />
            </div>

            {/* Nexus */}
            <div className="flex-1 text-center">
              <div className="text-indigo-200 text-sm font-bold mb-2 uppercase tracking-wide">Horizon Nexus</div>
              <div className="bg-indigo-600 border border-indigo-500 p-4 rounded-lg shadow-inner font-bold border-2">API Gateway & Webhooks</div>
            </div>

            <div className="px-6 flex flex-col items-center">
              <span className="text-xs text-indigo-300 font-bold mb-1">CANONICAL</span>
              <ArrowRight className="text-indigo-300 w-8 h-8" />
              <span className="text-xs text-blue-400 font-bold mt-1">OUTBOUND</span>
              <ArrowLeft className="text-blue-400 w-8 h-8" />
            </div>

            {/* Horizon Ecosystem */}
            <div className="flex-1 text-center">
              <div className="text-indigo-200 text-sm font-bold mb-2 uppercase tracking-wide">Horizon 360</div>
              <div className="bg-indigo-800 border border-indigo-700 p-4 rounded-lg">RawEvent Mesh & Workflow</div>
            </div>
          </div>
        </div>

        {/* Integrations List */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm mb-8 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
            <h3 className="text-lg font-bold text-slate-800">Configured Connectors</h3>
          </div>
          <div className="p-6 grid grid-cols-2 gap-6">
            {loading ? <p>Loading...</p> : integrations.length === 0 ? <p className="text-slate-500">No integrations configured.</p> : integrations.map(int => (
              <div key={int.id} className="border border-slate-200 p-5 rounded-lg hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="font-bold text-lg text-slate-900">{int.name}</h4>
                    <span className="text-xs text-slate-500 font-mono bg-slate-100 px-2 py-1 rounded mt-1 inline-block">{int.provider}</span>
                  </div>
                  <span className={`px-3 py-1 text-xs font-bold rounded-full ${int.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {int.status.toUpperCase()}
                  </span>
                </div>
                <div className="text-sm text-slate-600 flex justify-between items-center border-t pt-4">
                  <span>Direction: <strong className="text-slate-800 capitalize">{int.direction.replace('_', '-')}</strong></span>
                  <span className="text-xs text-slate-400">ID: {int.id.split('-')[0]}...</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Logs */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
            <h3 className="text-lg font-bold text-slate-800">Integration Activity Logs</h3>
          </div>
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Timestamp</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Integration</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Direction</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Event Type</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {loading ? (
                <tr><td colSpan={5} className="px-6 py-4 text-center text-sm text-slate-500">Loading...</td></tr>
              ) : logs.length === 0 ? (
                <tr><td colSpan={5} className="px-6 py-4 text-center text-sm text-slate-500">No integration logs found.</td></tr>
              ) : (
                logs.map(log => (
                  <tr key={log.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">{new Date(log.timestamp).toLocaleString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-slate-900">{log.integration_name}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-xs font-bold px-2 py-1 rounded ${log.direction === 'inbound' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                        {log.direction.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700 font-mono">{log.event_type}</td>
                    <td className="px-6 py-4 whitespace-nowrap flex items-center">
                      {log.status === 'success' ? <CheckCircle className="w-4 h-4 text-green-500 mr-2" /> : <XCircle className="w-4 h-4 text-red-500 mr-2" />}
                      <span className="text-sm font-medium text-slate-900 capitalize">{log.status}</span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
