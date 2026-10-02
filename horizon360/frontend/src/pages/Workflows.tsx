import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { horizonApi } from '../api';
import { Plus, ArrowLeft, Save, Zap, Search, Download, Star, Filter, Briefcase, Shield, Users, AlertTriangle, Clock } from 'lucide-react';
import { ReactFlow, Controls, Background, applyNodeChanges, applyEdgeChanges, addEdge, Node, Edge, Connection } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { RuleBuilder, RuleNode } from '../components/RuleBuilder';
import { SLAPolicyBuilder } from '../components/SLAPolicyBuilder';

// --- Custom Nodes ---
const CustomNode = ({ data }: any) => {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-white border-2 border-indigo-200 min-w-[150px]">
      <div className="flex items-center">
        <div className="rounded-full w-8 h-8 flex items-center justify-center bg-indigo-100 text-indigo-600 mr-3">
          {data.type === 'trigger' ? <Zap size={14} /> : 
           data.type === 'approval' ? <Shield size={14} /> : 
           data.type === 'ai_action' ? <Star size={14} /> : 
           <Briefcase size={14} />}
        </div>
        <div>
          <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">{data.type || 'Node'}</div>
          <div className="text-sm font-bold text-gray-800">{data.label}</div>
        </div>
      </div>
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

export const Workflows = () => {
  const navigate = useNavigate();
  const [currentTab, setCurrentTab] = useState<'my_flows' | 'marketplace'>('my_flows');
  
  // Data
  const [flows, setFlows] = useState<any[]>([]);
  const [executions, setExecutions] = useState<any[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Designer State
  const [activeFlow, setActiveFlow] = useState<any | null>(null);
  const [activeVersion, setActiveVersion] = useState<any | null>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [showSLABuilder, setShowSLABuilder] = useState(false);

  // Search/Filter for marketplace
  const [searchQuery, setSearchQuery] = useState('');

  const fetchData = async () => {
    try {
      setLoading(true);
      const [flowsData, execData, tmplData] = await Promise.all([
        horizonApi.getV2Flows(),
        horizonApi.getV2Executions(),
        horizonApi.getV2Templates()
      ]);
      setFlows(Array.isArray(flowsData) ? flowsData : flowsData.results || []);
      setExecutions(Array.isArray(execData) ? execData : execData.results || []);
      setTemplates(Array.isArray(tmplData) ? tmplData : tmplData.results || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openDesigner = async (flow: any) => {
    setActiveFlow(flow);
    if (flow.latest_version) {
      setActiveVersion(flow.latest_version);
      
      const rfNodes: Node[] = (flow.latest_version.nodes || []).map((n: any) => {
        let nodeConfig = { ...n.config };
        
        // Inject FlowDefinition properties into the trigger node for the UI to edit
        if (n.node_type === 'trigger') {
          nodeConfig = {
            ...nodeConfig,
            trigger_type: flow.trigger_type || 'event',
            trigger_event: flow.trigger_event || '',
            trigger_schedule: flow.trigger_schedule || '',
            ...flow.trigger_config
          };
        }

        return {
          id: n.canvas_node_id,
          type: 'custom',
          position: { x: n.position_x, y: n.position_y },
          data: { label: n.label, type: n.node_type, config: nodeConfig }
        };
      });
      
      const rfEdges: Edge[] = (flow.latest_version.edges || []).map((e: any) => ({
        id: e.edge_id,
        source: e.source_node,
        target: e.target_node,
        sourceHandle: e.source_handle || undefined,
        label: e.label || undefined,
        animated: true,
        style: { stroke: '#6366f1' }
      }));
      
      setNodes(rfNodes);
      setEdges(rfEdges);
    } else {
      setNodes([]);
      setEdges([]);
    }
  };

  const closeDesigner = () => {
    setActiveFlow(null);
    setActiveVersion(null);
    fetchData(); // refresh in case things changed
  };

  const installTemplate = async (template: any) => {
    try {
      const newFlow = await horizonApi.createV2Flow({
        name: `${template.name} (Copy)`,
        description: template.description,
        category: 'cross_biom',
        trigger_type: 'event',
        trigger_event: template.template_data.trigger || 'manual',
        is_active: false
      });
      alert(`Successfully installed template! You can now configure it in 'My Flows'.`);
      setCurrentTab('my_flows');
      fetchData();
    } catch(e) {
      alert('Error installing template.');
      console.error(e);
    }
  };

  const onNodesChange = useCallback((changes: any) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes: any) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);
  const onConnect = useCallback((connection: Connection) => setEdges((eds) => addEdge({ ...connection, animated: true, style: { stroke: '#6366f1' } }, eds)), []);

  const saveCanvas = async () => {
    if (!activeVersion) return;
    try {
      await horizonApi.saveV2FlowCanvas(activeVersion.id, nodes, edges);
      
      // Look for the trigger node to save its specific FlowDefinition settings
      const triggerNode = nodes.find(n => n.data.type === 'trigger');
      if (triggerNode) {
        const config: any = triggerNode.data.config || {};
        await horizonApi.updateV2FlowTrigger(activeVersion.flow, {
          trigger_type: config.trigger_type || 'event',
          trigger_event: config.trigger_event || '',
          trigger_schedule: config.trigger_schedule || '',
          trigger_config: config
        });
      }
      
      alert('Canvas & Workflow Settings saved successfully!');
    } catch (e) {
      console.error(e);
      alert('Failed to save workflow.');
    }
  };

  // --- Node Configuration State ---
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  
  const onNodeClick = useCallback((_: any, node: Node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const updateSelectedNode = (field: string, value: any, isConfig = true) => {
    if (!selectedNode) return;
    
    setNodes(nds => nds.map(n => {
      if (n.id === selectedNode.id) {
        const updated = { ...n };
        if (isConfig) {
          updated.data = { ...updated.data, config: { ...(updated.data.config as any || {}), [field]: value } };
        } else {
          updated.data = { ...updated.data, [field]: value };
        }
        setSelectedNode(updated); // keep local state in sync
        return updated;
      }
      return n;
    }));
  };

  // ─── Designer View ──────────────────────────────────────────────
  if (activeFlow) {
    return (
      <div className="flex flex-col h-full w-full">
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center z-10 shadow-sm shrink-0">
          <div className="flex items-center space-x-4">
            <button onClick={closeDesigner} className="p-2 hover:bg-gray-100 rounded-full text-gray-500">
              <ArrowLeft size={20} />
            </button>
            <div>
              <h2 className="text-xl font-bold text-gray-900">{activeFlow.name}</h2>
              <p className="text-xs text-gray-500">Trigger: {activeFlow.trigger_event}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => setShowSLABuilder(true)} className="flex items-center px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 font-medium text-sm shadow-sm">
              <Clock size={16} className="mr-2 text-indigo-600" />
              SLA Policies
            </button>
            <button onClick={saveCanvas} className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 font-medium text-sm">
              <Save size={16} className="mr-2" />
              Save Layout
            </button>
          </div>
        </div>
        
        <div className="flex-1 bg-gray-50 w-full h-full relative flex overflow-hidden">
          <div className="flex-1 h-full relative">
            <ReactFlow 
              nodes={nodes} 
              edges={edges} 
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              onPaneClick={onPaneClick}
              nodeTypes={nodeTypes}
              fitView
            >
              <Background color="#ccc" gap={16} />
              <Controls />
            </ReactFlow>
          </div>

          {/* Node Configuration Panel */}
          {selectedNode && (
            <div className="w-80 bg-white border-l border-gray-200 h-full flex flex-col shadow-lg shrink-0 z-20">
              <div className="p-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
                <h3 className="font-bold text-gray-900">Configure Node</h3>
                <span className="text-xs font-mono bg-gray-200 px-2 py-1 rounded text-gray-600 uppercase tracking-wider">{selectedNode.data.type as string}</span>
              </div>
              <div className="p-6 flex-1 overflow-y-auto space-y-6">
                
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">Node Label</label>
                  <input 
                    type="text" 
                    className="w-full border border-gray-300 rounded p-2 text-sm focus:ring-indigo-500 focus:border-indigo-500"
                    value={selectedNode.data.label as string}
                    onChange={(e) => updateSelectedNode('label', e.target.value, false)}
                  />
                </div>

                {selectedNode.data.type === 'trigger' && (
                  <div className="bg-gray-50 p-4 border border-gray-200 rounded-lg mt-4">
                    <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">Trigger Type</label>
                    <select 
                      className="w-full border border-gray-300 rounded p-2 text-sm mb-3 focus:ring-indigo-500 focus:border-indigo-500"
                      value={(selectedNode.data.config as any)?.trigger_type || 'event'}
                      onChange={(e) => updateSelectedNode('trigger_type', e.target.value)}
                    >
                      <option value="event">System Event</option>
                      <option value="webhook">Inbound Webhook</option>
                      <option value="schedule">Cron Schedule</option>
                    </select>

                    {(selectedNode.data.config as any)?.trigger_type === 'event' && (
                      <>
                        <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">Event Topic</label>
                        <input 
                          type="text" 
                          className="w-full border border-gray-300 rounded p-2 text-sm font-mono mb-3"
                          placeholder="e.g. deal.won"
                          value={(selectedNode.data.config as any)?.trigger_event || ''}
                          onChange={(e) => updateSelectedNode('trigger_event', e.target.value)}
                        />
                      </>
                    )}

                    {(selectedNode.data.config as any)?.trigger_type === 'webhook' && (
                      <>
                        <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">Webhook Target URL</label>
                        <div className="bg-gray-900 text-green-400 font-mono text-[10px] p-2 rounded mb-3 break-all">
                          {window.location.origin}/api/v2/flow-engine/webhooks/{activeVersion?.flow}/
                        </div>
                        <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">Secret Key (Optional)</label>
                        <input 
                          type="text" 
                          className="w-full border border-gray-300 rounded p-2 text-sm font-mono mb-3"
                          placeholder="e.g. super-secret-123"
                          value={(selectedNode.data.config as any)?.secret || ''}
                          onChange={(e) => updateSelectedNode('secret', e.target.value)}
                        />
                      </>
                    )}

                    {(selectedNode.data.config as any)?.trigger_type === 'schedule' && (
                      <>
                        <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">Cron Expression</label>
                        <input 
                          type="text" 
                          className="w-full border border-gray-300 rounded p-2 text-sm font-mono mb-3"
                          placeholder="e.g. */5 * * * *"
                          value={(selectedNode.data.config as any)?.trigger_schedule || ''}
                          onChange={(e) => updateSelectedNode('trigger_schedule', e.target.value)}
                        />
                        <p className="text-[10px] text-gray-500">Standard 5-part cron syntax (minute hour day month weekday). Evaluated in UTC.</p>
                      </>
                    )}
                  </div>
                )}

                {selectedNode.data.type === 'action' && (
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">BIOM Action</label>
                    <select 
                      className="w-full border border-gray-300 rounded p-2 text-sm focus:ring-indigo-500 focus:border-indigo-500"
                      value={(selectedNode.data.config as any)?.action_type || ''}
                      onChange={(e) => updateSelectedNode('action_type', e.target.value)}
                    >
                      <option value="">Select an action...</option>
                      <option value="create_invoice">Create Invoice (Finance)</option>
                      <option value="create_project">Create Project (Operations)</option>
                      <option value="create_ticket">Create Support Ticket (Service)</option>
                      <option value="create_purchase_order">Create PO (Vendor)</option>
                      <option value="setup_payroll">Setup Payroll (HRMS)</option>
                    </select>
                  </div>
                )}

                {selectedNode.data.type === 'ai_action' && (
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">AI Prompt Template</label>
                    <p className="text-[11px] text-gray-500 mb-2">Use {'{{variable}}'} to inject context.</p>
                    <textarea 
                      className="w-full border border-gray-300 rounded p-2 text-sm focus:ring-indigo-500 focus:border-indigo-500 font-mono"
                      rows={5}
                      value={(selectedNode.data.config as any)?.prompt_template || ''}
                      onChange={(e) => updateSelectedNode('prompt_template', e.target.value)}
                      placeholder="Analyze the following payload: {{trigger.payload}}"
                    />
                    
                    <label className="block text-xs font-bold text-gray-700 mt-4 mb-2 uppercase tracking-wide">Output Variable Name</label>
                    <input 
                      type="text" 
                      className="w-full border border-gray-300 rounded p-2 text-sm focus:ring-indigo-500 focus:border-indigo-500 font-mono"
                      value={(selectedNode.data.config as any)?.output_variable || 'ai_output'}
                      onChange={(e) => updateSelectedNode('output_variable', e.target.value)}
                    />
                  </div>
                )}

                {selectedNode.data.type === 'approval' && (
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">Approval Title</label>
                    <input 
                      type="text" 
                      className="w-full border border-gray-300 rounded p-2 text-sm focus:ring-indigo-500 focus:border-indigo-500 mb-4"
                      value={(selectedNode.data.config as any)?.title || ''}
                      onChange={(e) => updateSelectedNode('title', e.target.value)}
                    />
                    
                    <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">Description</label>
                    <textarea 
                      className="w-full border border-gray-300 rounded p-2 text-sm focus:ring-indigo-500 focus:border-indigo-500"
                      rows={3}
                      value={(selectedNode.data.config as any)?.description || ''}
                      onChange={(e) => updateSelectedNode('description', e.target.value)}
                    />
                  </div>
                )}

                {selectedNode.data.type === 'condition' && (
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">Logic Builder</label>
                    <RuleBuilder 
                      ruleTree={(selectedNode.data.config as any)?.rule_tree || { type: 'group', logic: 'AND', rules: [] }}
                      onChange={(newTree) => updateSelectedNode('rule_tree', newTree)}
                    />
                  </div>
                )}

              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ─── Main View ──────────────────────────────────────────────────
  return (
    <div className="flex-1 bg-gray-50 h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-6">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">Horizon Flow Engine</h2>
            <p className="text-gray-500 mt-1">Level 6 Orchestration & Cross-BIOM Automation</p>
          </div>
          <button className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
            <Plus className="w-4 h-4 mr-2" />
            New Workflow
          </button>
        </div>

        {/* Tabs */}
        <div className="max-w-6xl mx-auto mt-6 flex space-x-6 border-b border-gray-200">
          <button 
            className={`pb-3 font-medium text-sm border-b-2 transition-colors ${currentTab === 'my_flows' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            onClick={() => setCurrentTab('my_flows')}
          >
            My Flows
          </button>
          <button 
            className={`pb-3 font-medium text-sm border-b-2 transition-colors flex items-center ${currentTab === 'marketplace' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            onClick={() => setCurrentTab('marketplace')}
          >
            Marketplace <span className="ml-2 bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full text-[10px] font-bold">NEW</span>
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-6xl mx-auto">
          
          {/* ─── My Flows Tab ─── */}
          {currentTab === 'my_flows' && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
                {loading ? <p>Loading workflows...</p> : flows.map(wf => (
                  <div key={wf.id} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow cursor-pointer" onClick={() => openDesigner(wf)}>
                    <div className="flex justify-between items-start mb-4">
                      <div className="w-12 h-12 bg-indigo-50 border border-indigo-100 rounded-lg flex items-center justify-center text-indigo-600">
                        <Zap size={20} />
                      </div>
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${wf.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                        {wf.is_active ? 'Active' : 'Draft'}
                      </span>
                    </div>
                    <h3 className="text-lg font-bold mb-1">{wf.name}</h3>
                    <p className="text-sm text-gray-500 mb-4 line-clamp-2 min-h-[40px]">{wf.description || 'No description provided.'}</p>
                    
                    <div className="flex items-center justify-between text-sm pt-4 border-t border-gray-100">
                      <span className="text-gray-500 font-mono text-[11px] bg-gray-100 px-2 py-1 rounded">{wf.trigger_event || 'manual'}</span>
                      <span className="text-indigo-600 font-medium text-xs">Edit Canvas &rarr;</span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
                <div className="p-4 border-b border-gray-200 bg-gray-50">
                  <h3 className="text-lg font-semibold">Execution History</h3>
                </div>
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Workflow</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Trigger Context</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {loading ? (
                      <tr><td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500">Loading...</td></tr>
                    ) : executions.length === 0 ? (
                      <tr><td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500">No executions found.</td></tr>
                    ) : (
                      executions.map((exec) => (
                        <tr 
                          key={exec.id} 
                          className="hover:bg-gray-50 cursor-pointer transition-colors"
                          onClick={() => navigate(`/executions/${exec.id}`)}
                        >
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-indigo-600 hover:text-indigo-900">
                            {exec.flow ? exec.flow.name : 'Unknown'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              exec.status === 'completed' ? 'bg-green-100 text-green-800' :
                              exec.status === 'failed' ? 'bg-red-100 text-red-800' :
                              exec.status === 'waiting' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-blue-100 text-blue-800'
                            }`}>
                              {exec.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500 font-mono">
                            {exec.trigger_payload?.event_id || 'manual_trigger'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(exec.created_at).toLocaleString()}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* ─── Marketplace Tab ─── */}
          {currentTab === 'marketplace' && (
            <div>
              <div className="flex justify-between items-center mb-8">
                <div>
                  <h3 className="text-xl font-bold">Automation Marketplace</h3>
                  <p className="text-gray-500 text-sm">Discover and install pre-built cross-BIOM automation templates.</p>
                </div>
                <div className="relative w-72">
                  <input 
                    type="text" 
                    placeholder="Search templates..." 
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                  <Search className="absolute left-3 top-2.5 text-gray-400 w-4 h-4" />
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {templates
                  .filter(t => t.name.toLowerCase().includes(searchQuery.toLowerCase()) || t.description.toLowerCase().includes(searchQuery.toLowerCase()))
                  .map(template => (
                  <div key={template.id} className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm flex flex-col">
                    <div className="p-6 flex-1">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-lg flex items-center justify-center">
                            {template.icon === 'briefcase' ? <Briefcase size={20} /> :
                             template.icon === 'shield' ? <Shield size={20} /> :
                             template.icon === 'users' ? <Users size={20} /> :
                             <Zap size={20} />}
                          </div>
                          <div>
                            <h4 className="font-bold text-gray-900">{template.name}</h4>
                            <div className="flex items-center text-xs text-gray-500 mt-1">
                              <span className="flex items-center text-amber-500 mr-3"><Star size={12} className="mr-1 fill-current" /> {template.rating}</span>
                              <span>{template.install_count.toLocaleString()} installs</span>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <p className="text-sm text-gray-600 mb-6 min-h-[40px]">{template.description}</p>
                      
                      <div className="flex flex-wrap gap-2 mb-4">
                        {template.tags?.map((tag: string, idx: number) => (
                          <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-600 text-[10px] font-bold uppercase tracking-wider rounded">
                            {tag}
                          </span>
                        ))}
                      </div>

                      <div className="flex items-center text-xs text-gray-500 border-t border-gray-100 pt-4">
                        <span className="font-semibold text-gray-700 mr-2">Integrates:</span>
                        <div className="flex space-x-2">
                          {template.source_bioms?.concat(template.target_bioms)?.map((b: string, i: number) => (
                            <span key={i} className="text-indigo-600">{b}{i < (template.source_bioms.length + template.target_bioms.length - 1) ? ',' : ''}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-between items-center">
                      <div className="text-xs text-gray-500 font-mono truncate max-w-[200px]">Trigger: {template.template_data.trigger}</div>
                      <button 
                        onClick={() => installTemplate(template)}
                        className="flex items-center px-4 py-2 bg-white border border-gray-300 rounded shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 hover:text-indigo-600 transition-colors"
                      >
                        <Download size={14} className="mr-2" />
                        Install Template
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      
      {showSLABuilder && activeFlow && (
        <SLAPolicyBuilder 
          flowId={activeFlow.id} 
          nodes={nodes} 
          onClose={() => setShowSLABuilder(false)} 
        />
      )}
    </div>
  );
};
