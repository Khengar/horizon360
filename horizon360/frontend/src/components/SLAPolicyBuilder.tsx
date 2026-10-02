import React, { useState, useEffect } from 'react';
import { Shield, Plus, X, Trash2, Clock, AlertTriangle } from 'lucide-react';
import { horizonApi } from '../api';

export const SLAPolicyBuilder = ({ flowId, nodes, onClose }: { flowId: string, nodes: any[], onClose: () => void }) => {
  const [policies, setPolicies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  
  const [scope, setScope] = useState('flow');
  const [targetNodeId, setTargetNodeId] = useState('');
  const [warningMins, setWarningMins] = useState(60);
  const [breachMins, setBreachMins] = useState(120);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchPolicies();
  }, [flowId]);

  const fetchPolicies = async () => {
    try {
      const data = await horizonApi.getSLAPolicies(flowId);
      setPolicies(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    setIsSubmitting(true);
    try {
      await horizonApi.createSLAPolicy({
        flow: flowId,
        scope,
        target_node_id: scope === 'node' ? targetNodeId : '',
        warning_threshold_minutes: warningMins,
        breach_threshold_minutes: breachMins,
        is_active: true
      });
      setShowForm(false);
      setScope('flow');
      setTargetNodeId('');
      fetchPolicies();
    } catch (e) {
      console.error(e);
      alert('Failed to create SLA Policy.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this SLA policy?')) return;
    try {
      await horizonApi.deleteSLAPolicy(id);
      fetchPolicies();
    } catch (e) {
      console.error(e);
      alert('Failed to delete SLA Policy.');
    }
  };

  const getNodeLabel = (id: string) => {
    const node = nodes.find(n => n.id === id || n.canvas_node_id === id);
    return node?.data?.label || id;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex justify-between items-center p-6 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center">
            <Shield className="w-6 h-6 text-indigo-600 mr-2" />
            <h2 className="text-xl font-bold text-gray-800">SLA Policy Builder</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={24} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto flex-1">
          {loading ? (
            <div className="text-center py-8 text-gray-500">Loading policies...</div>
          ) : (
            <>
              {policies.length === 0 ? (
                <div className="text-center py-8 bg-gray-50 rounded-lg border border-dashed border-gray-300 mb-6">
                  <Shield className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-500 font-medium">No SLA policies defined for this flow.</p>
                  <p className="text-gray-400 text-sm mt-1">Set time limits on approvals, human tasks, or the entire flow.</p>
                </div>
              ) : (
                <div className="space-y-4 mb-6">
                  {policies.map(policy => (
                    <div key={policy.id} className="flex justify-between items-center p-4 border border-gray-200 rounded-lg bg-white shadow-sm">
                      <div>
                        <div className="flex items-center mb-1">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase mr-2 ${
                            policy.scope === 'flow' ? 'bg-indigo-100 text-indigo-700' : 'bg-blue-100 text-blue-700'
                          }`}>
                            {policy.scope}
                          </span>
                          <span className="font-bold text-gray-800">
                            {policy.scope === 'flow' ? 'Entire Flow Execution' : getNodeLabel(policy.target_node_id)}
                          </span>
                        </div>
                        <div className="flex space-x-4 text-sm text-gray-500 mt-2">
                          <span className="flex items-center">
                            <Clock className="w-4 h-4 mr-1 text-yellow-500" />
                            Warning: {policy.warning_threshold_minutes}m
                          </span>
                          <span className="flex items-center">
                            <AlertTriangle className="w-4 h-4 mr-1 text-red-500" />
                            Breach: {policy.breach_threshold_minutes}m
                          </span>
                        </div>
                      </div>
                      <button onClick={() => handleDelete(policy.id)} className="text-gray-400 hover:text-red-500 p-2">
                        <Trash2 size={18} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {showForm ? (
                <div className="bg-gray-50 p-5 rounded-lg border border-gray-200">
                  <h3 className="font-bold text-gray-800 mb-4">Create New Policy</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Policy Scope</label>
                      <select 
                        value={scope} 
                        onChange={e => setScope(e.target.value)}
                        className="w-full p-2 border border-gray-300 rounded focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                      >
                        <option value="flow">Entire Workflow</option>
                        <option value="node">Specific Node (e.g. Approval)</option>
                      </select>
                    </div>
                    
                    {scope === 'node' && (
                      <div>
                        <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Target Node</label>
                        <select 
                          value={targetNodeId} 
                          onChange={e => setTargetNodeId(e.target.value)}
                          className="w-full p-2 border border-gray-300 rounded focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                        >
                          <option value="">Select a node...</option>
                          {nodes.filter(n => n.data?.type !== 'trigger' && n.data?.type !== 'end').map(n => (
                            <option key={n.id} value={n.id}>{n.data?.label || n.id}</option>
                          ))}
                        </select>
                      </div>
                    )}
                    
                    <div className="flex space-x-4">
                      <div className="flex-1">
                        <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Warning Threshold (Mins)</label>
                        <input 
                          type="number" 
                          value={warningMins} 
                          onChange={e => setWarningMins(parseInt(e.target.value) || 0)}
                          className="w-full p-2 border border-gray-300 rounded focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                        />
                      </div>
                      <div className="flex-1">
                        <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Breach Threshold (Mins)</label>
                        <input 
                          type="number" 
                          value={breachMins} 
                          onChange={e => setBreachMins(parseInt(e.target.value) || 0)}
                          className="w-full p-2 border border-gray-300 rounded focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-5 flex justify-end space-x-3">
                    <button 
                      onClick={() => setShowForm(false)}
                      className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium text-sm"
                    >
                      Cancel
                    </button>
                    <button 
                      onClick={handleCreate}
                      disabled={isSubmitting || (scope === 'node' && !targetNodeId)}
                      className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 font-medium text-sm disabled:opacity-50"
                    >
                      {isSubmitting ? 'Saving...' : 'Save Policy'}
                    </button>
                  </div>
                </div>
              ) : (
                <button 
                  onClick={() => setShowForm(true)}
                  className="w-full py-3 border-2 border-dashed border-indigo-300 text-indigo-600 rounded-lg font-bold flex items-center justify-center hover:bg-indigo-50 hover:border-indigo-400 transition-colors"
                >
                  <Plus size={18} className="mr-2" />
                  Add SLA Policy
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
