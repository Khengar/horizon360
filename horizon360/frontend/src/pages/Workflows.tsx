import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';
import { ArrowDown, Check, X, Plus } from 'lucide-react';

export const Workflows = () => {
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [executions, setExecutions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [showCreate, setShowCreate] = useState(false);
  const [newWorkflow, setNewWorkflow] = useState({
    name: '',
    trigger_event: '',
    action_type: '',
    source_biom: '',
    destination_biom: ''
  });

  const [templates, setTemplates] = useState<any[]>([]);

  const fetchData = () => {
    Promise.all([
      horizonApi.getWorkflows(),
      horizonApi.getWorkflowExecutions(),
      horizonApi.getWorkflowTemplates()
    ]).then(([wfData, execData, tmplData]) => {
      setWorkflows(wfData);
      setExecutions(execData);
      setTemplates(tmplData);
      setLoading(false);
    }).catch(console.error);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const toggleWorkflow = async (id: number, currentStatus: boolean) => {
    await horizonApi.updateWorkflow(id, { is_active: !currentStatus });
    fetchData();
  };

  const handleCreate = async () => {
    await horizonApi.createWorkflow(newWorkflow);
    setShowCreate(false);
    setNewWorkflow({ name: '', trigger_event: '', action_type: '', source_biom: '', destination_biom: '' });
    fetchData();
  };

  return (
    <div className="flex-1 p-8 bg-gray-50 h-full overflow-y-auto">
      <div className="max-w-6xl w-full mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-3xl font-bold text-gray-900">Horizon Flow</h2>
          <button 
            onClick={() => setShowCreate(!showCreate)}
            className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Workflow
          </button>
        </div>

        {showCreate && (
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8">
            <h3 className="text-lg font-semibold mb-4">Create New Workflow</h3>
            
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-500 mb-2">Quick Templates</h4>
              <div className="flex flex-wrap gap-2">
                {templates.map((t, idx) => (
                  <button 
                    key={idx}
                    onClick={() => setNewWorkflow({
                      name: t.name,
                      trigger_event: t.trigger_event,
                      action_type: t.action_type,
                      source_biom: t.source_biom,
                      destination_biom: t.destination_biom
                    })}
                    className="text-xs bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded border border-indigo-100 hover:bg-indigo-100 transition-colors"
                  >
                    <span className="font-bold mr-1">{t.group}:</span> {t.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4 pt-4 border-t border-gray-100">
              <input type="text" placeholder="Workflow Name" className="border p-2 rounded"
                value={newWorkflow.name} onChange={e => setNewWorkflow({...newWorkflow, name: e.target.value})} />
              <input type="text" placeholder="Trigger Event (e.g. deal.won)" className="border p-2 rounded"
                value={newWorkflow.trigger_event} onChange={e => setNewWorkflow({...newWorkflow, trigger_event: e.target.value})} />
              <input type="text" placeholder="Source BIOM (e.g. Sales)" className="border p-2 rounded"
                value={newWorkflow.source_biom} onChange={e => setNewWorkflow({...newWorkflow, source_biom: e.target.value})} />
              <input type="text" placeholder="Destination BIOM (e.g. Finance)" className="border p-2 rounded"
                value={newWorkflow.destination_biom} onChange={e => setNewWorkflow({...newWorkflow, destination_biom: e.target.value})} />
              <input type="text" placeholder="Action Type (e.g. create_invoice)" className="border p-2 rounded col-span-2"
                value={newWorkflow.action_type} onChange={e => setNewWorkflow({...newWorkflow, action_type: e.target.value})} />
            </div>
            <button onClick={handleCreate} className="px-4 py-2 bg-green-600 text-white rounded-md">Save Workflow</button>
          </div>
        )}

        <div className="space-y-8 mb-8">
          {loading ? <p>Loading workflows...</p> : workflows.map(wf => (
            <div key={wf.id} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="text-xl font-bold">{wf.name}</h3>
                  <p className="text-gray-500 text-sm mt-1">Cross-BIOM Automation</p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${wf.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                    {wf.is_active ? 'Active' : 'Disabled'}
                  </span>
                  <button 
                    onClick={() => toggleWorkflow(wf.id, wf.is_active)}
                    className="text-xs px-3 py-1 border rounded bg-gray-50 hover:bg-gray-100"
                  >
                    Toggle
                  </button>
                </div>
              </div>

              {/* Visual Flow Representation */}
              <div className="flex flex-col items-center justify-center space-y-2 py-4 bg-gray-50 rounded-lg border border-gray-100">
                {/* Source */}
                <div className="flex flex-col items-center">
                  <div className="px-4 py-2 border-2 border-indigo-200 bg-white rounded-lg shadow-sm text-center min-w-[160px]">
                    <div className="text-xs font-bold text-indigo-600 uppercase tracking-wider">{wf.source_biom || 'Trigger'}</div>
                    <div className="font-semibold text-gray-900">{wf.trigger_event}</div>
                  </div>
                </div>

                <ArrowDown className="text-gray-400 w-5 h-5" />
                
                {/* Condition (Optional) */}
                {wf.condition_field && (
                  <>
                    <div className="px-4 py-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
                      Condition: {wf.condition_field} {wf.condition_operator} {wf.condition_value}
                    </div>
                    <ArrowDown className="text-gray-400 w-5 h-5" />
                  </>
                )}

                {/* Destination */}
                <div className="flex flex-col items-center">
                  <div className="px-4 py-2 border-2 border-green-200 bg-white rounded-lg shadow-sm text-center min-w-[160px]">
                    <div className="text-xs font-bold text-green-600 uppercase tracking-wider">{wf.destination_biom || 'Action'}</div>
                    <div className="font-semibold text-gray-900">{wf.action_type}</div>
                  </div>
                </div>
                
                <ArrowDown className="text-gray-400 w-5 h-5" />
                
                <div className="flex items-center space-x-1 text-sm font-semibold text-gray-600">
                  <Check className="w-4 h-4 text-green-500" />
                  <span>RESULT</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden mt-8">
          <div className="p-4 border-b border-gray-200 bg-gray-50">
            <h3 className="text-lg font-semibold">Execution History</h3>
          </div>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Workflow</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Event ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Error</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr><td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500">Loading...</td></tr>
              ) : executions.length === 0 ? (
                <tr><td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500">No executions found.</td></tr>
              ) : (
                executions.map((exec) => (
                  <tr key={exec.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{exec.workflow_name || `Workflow #${exec.workflow}`}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        exec.status === 'success' ? 'bg-green-100 text-green-800' :
                        exec.status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {exec.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{exec.raw_event}</td>
                    <td className="px-6 py-4 text-sm text-red-600 truncate max-w-xs">{exec.error_message || '-'}</td>
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
