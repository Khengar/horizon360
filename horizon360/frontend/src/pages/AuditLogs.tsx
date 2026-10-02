import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { Shield, Search, Filter, Clock, CheckCircle, XCircle, Play, User, Activity } from 'lucide-react';
import { horizonApi } from '../api';

const AuditLogs = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const data = await horizonApi.getFlowAuditLogs();
        setLogs(data);
      } catch (e) {
        console.error("Failed to fetch audit logs", e);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  const getEventIcon = (eventType: string) => {
    if (eventType.includes('completed')) return <CheckCircle className="w-5 h-5 text-green-500" />;
    if (eventType.includes('failed')) return <XCircle className="w-5 h-5 text-red-500" />;
    if (eventType.includes('started')) return <Play className="w-5 h-5 text-blue-500" />;
    return <Activity className="w-5 h-5 text-gray-500" />;
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Shield className="w-7 h-7 mr-3 text-indigo-600" />
            System Audit Trail
          </h1>
          <p className="text-gray-500 mt-1">Immutable record of all workflow engine events.</p>
        </div>
        
        <div className="flex gap-4">
          <div className="relative">
            <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input 
              type="text" 
              placeholder="Search logs..." 
              className="pl-10 pr-4 py-2 border rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <button className="flex items-center px-4 py-2 bg-white border rounded-md shadow-sm text-gray-700 hover:bg-gray-50">
            <Filter className="w-4 h-4 mr-2" />
            Filter
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-500 border-b border-gray-200">
              <tr>
                <th className="px-6 py-4 font-medium">Timestamp</th>
                <th className="px-6 py-4 font-medium">Event Type</th>
                <th className="px-6 py-4 font-medium">Actor</th>
                <th className="px-6 py-4 font-medium">Description</th>
                <th className="px-6 py-4 font-medium">Execution ID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {loading ? (
                <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-500">Loading audit trail...</td></tr>
              ) : logs.length === 0 ? (
                <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-500">No audit events found.</td></tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-gray-900">
                        <Clock className="w-4 h-4 mr-2 text-gray-400" />
                        {log.created_at ? format(new Date(log.created_at), 'MMM d, yyyy HH:mm:ss') : ''}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getEventIcon(log.event_type)}
                        <span className="ml-2 font-medium text-gray-900">{log.event_type}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <User className="w-4 h-4 mr-2 text-gray-400" />
                        <span className="text-gray-900 capitalize">{log.actor_type}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-gray-600">{log.description}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {log.execution_id ? (
                        <a href={`/executions/${log.execution_id}`} className="text-indigo-600 hover:text-indigo-900 font-mono text-xs">
                          {log.execution_id.substring(0, 8)}...
                        </a>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
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

export default AuditLogs;
