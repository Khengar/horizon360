import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ReactFlow, Controls, Background, Node, Edge } from '@xyflow/react';
import { horizonApi } from '../api';
import { ArrowLeft, Clock, Zap, Star, Shield, Briefcase, CheckCircle, XCircle, AlertCircle, Loader } from 'lucide-react';
import '@xyflow/react/dist/style.css';

const DebuggerNode = ({ data }: any) => {
  // Determine border and bg colors based on execution status
  const status = data.stepStatus || 'pending';
  let borderClass = 'border-gray-200';
  let bgClass = 'bg-white';
  
  if (status === 'completed') {
    borderClass = 'border-green-500';
    bgClass = 'bg-green-50';
  } else if (status === 'failed') {
    borderClass = 'border-red-500';
    bgClass = 'bg-red-50';
  } else if (status === 'running') {
    borderClass = 'border-blue-500';
    bgClass = 'bg-blue-50';
  } else if (status === 'waiting') {
    borderClass = 'border-yellow-500';
    bgClass = 'bg-yellow-50';
  }

  return (
    <div className={`px-4 py-2 shadow-lg rounded-md border-2 min-w-[160px] ${borderClass} ${bgClass} transition-all`}>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center">
          <div className="rounded-full w-6 h-6 flex items-center justify-center bg-white text-gray-600 mr-2 shadow-sm border border-gray-100">
            {data.type === 'trigger' ? <Zap size={12} /> : 
             data.type === 'approval' ? <Shield size={12} /> : 
             data.type === 'ai_action' ? <Star size={12} /> : 
             <Briefcase size={12} />}
          </div>
          <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">{data.type}</div>
        </div>
        {/* Status Indicator Icon */}
        <div>
           {status === 'completed' && <CheckCircle size={14} className="text-green-600" />}
           {status === 'failed' && <XCircle size={14} className="text-red-600" />}
           {status === 'running' && <Loader size={14} className="text-blue-600 animate-spin" />}
           {status === 'waiting' && <AlertCircle size={14} className="text-yellow-600" />}
        </div>
      </div>
      <div className="text-sm font-bold text-gray-900 mt-1">{data.label}</div>
      {data.duration_ms && (
        <div className="text-[10px] text-gray-500 flex items-center mt-2 font-mono">
          <Clock size={10} className="mr-1" /> {data.duration_ms}ms
        </div>
      )}
    </div>
  );
};

const nodeTypes = {
  debugger: DebuggerNode,
};

export const ExecutionTrace = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [execution, setExecution] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  // Canvas State
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  
  // Selection State
  const [selectedStep, setSelectedStep] = useState<any>(null);

  useEffect(() => {
    const fetchTrace = async () => {
      try {
        const data = await horizonApi.getV2Execution(id!);
        setExecution(data);
        
        // Build the DAG from version_data
        const stepsByNodeId = data.steps.reduce((acc: any, step: any) => {
          acc[step.canvas_node_id] = step;
          return acc;
        }, {});

        const rfNodes = data.version_data.nodes.map((n: any) => {
          const step = stepsByNodeId[n.canvas_node_id];
          return {
            id: n.canvas_node_id,
            type: 'debugger',
            position: { x: n.position_x, y: n.position_y },
            data: { 
              label: n.label, 
              type: n.node_type, 
              config: n.config,
              stepStatus: step?.status || 'pending',
              duration_ms: step?.duration_ms || null,
              stepData: step || null
            }
          };
        });

        const rfEdges = data.version_data.edges.map((e: any) => {
          const sourceStep = stepsByNodeId[e.source_node];
          const animated = sourceStep?.status === 'running' || sourceStep?.status === 'waiting';
          const executed = sourceStep?.status === 'completed';
          
          return {
            id: e.edge_id,
            source: e.source_node,
            target: e.target_node,
            sourceHandle: e.source_handle,
            label: e.label,
            animated: animated,
            style: { 
              stroke: executed ? '#22c55e' : (animated ? '#3b82f6' : '#cbd5e1'), 
              strokeWidth: executed || animated ? 2 : 1 
            }
          };
        });

        setNodes(rfNodes);
        setEdges(rfEdges);
      } catch(e) {
        console.error("Failed to fetch execution trace", e);
      } finally {
        setLoading(false);
      }
    };

    fetchTrace();
  }, [id]);

  useEffect(() => {
    if (!id) return;
    
    // Connect to WebSocket
    const wsUrl = window.location.hostname === 'localhost' 
      ? `ws://localhost:8000/ws/executions/${id}/`
      : `ws://${window.location.hostname}:8000/ws/executions/${id}/`;
    const ws = new WebSocket(wsUrl);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WS Event:', data);
      
      // Update nodes dynamically
      setNodes((nds) => 
        nds.map((node) => {
          if (node.id === data.node_id) {
            return {
              ...node,
              data: {
                ...node.data,
                stepStatus: data.status,
                stepData: {
                  ...(node.data.stepData || {}),
                  status: data.status,
                  output_data: data.output || (node.data.stepData as any)?.output_data,
                  error_message: data.error || (node.data.stepData as any)?.error_message
                }
              }
            };
          }
          return node;
        })
      );
      
      // Also trigger a full refresh to get edges updated (lazy but effective)
      // or we could compute edges here. For now just update node states.
    };

    return () => {
      ws.close();
    };
  }, [id, setNodes]);

  if (loading && !execution) {
    return <div className="p-8 text-center text-gray-500">Loading trace...</div>;
  }

  if (!execution) return <div className="p-8 text-center text-red-500">Execution not found.</div>;

  const onNodeClick = (_: any, node: Node) => {
    setSelectedStep(node.data.stepData || { canvas_node_id: node.id, status: 'pending', input_data: null, output_data: null });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'waiting': return 'bg-yellow-100 text-yellow-800';
      case 'running': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="flex flex-col h-full w-full bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center shrink-0 shadow-sm z-10">
        <div className="flex items-center space-x-4">
          <button onClick={() => navigate('/workflows')} className="p-2 hover:bg-gray-100 rounded-full text-gray-500 transition-colors">
            <ArrowLeft size={20} />
          </button>
          <div>
            <h2 className="text-xl font-bold text-gray-900 flex items-center">
              Execution Trace
              <span className={`ml-3 px-2 py-0.5 text-[10px] font-bold uppercase rounded-full ${getStatusColor(execution.status)}`}>
                {execution.status}
              </span>
            </h2>
            <div className="text-xs text-gray-500 mt-1 flex items-center font-mono">
              <span className="mr-3">ID: {execution.id}</span>
              <span>Triggered: {new Date(execution.created_at).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Canvas Pane */}
        <div className="flex-1 relative">
          <ReactFlow 
            nodes={nodes} 
            edges={edges} 
            nodeTypes={nodeTypes}
            onNodeClick={onNodeClick}
            onPaneClick={() => setSelectedStep(null)}
            fitView
            proOptions={{ hideAttribution: true }}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable={true}
          >
            <Background color="#ccc" gap={16} />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>

        {/* Trace Inspector Sidebar */}
        {selectedStep && (
          <div className="w-96 bg-white border-l border-gray-200 shadow-xl z-20 flex flex-col shrink-0">
            <div className="p-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
              <div>
                <h3 className="font-bold text-gray-900">Step Inspector</h3>
                <p className="text-[10px] text-gray-500 font-mono mt-1">Node: {selectedStep.canvas_node_id}</p>
              </div>
              <span className={`px-2 py-1 text-[10px] font-bold uppercase rounded ${getStatusColor(selectedStep.status)}`}>
                {selectedStep.status}
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              
              {selectedStep.error_message && (
                <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <XCircle className="h-5 w-5 text-red-400" />
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-red-800">Execution Error</h3>
                      <div className="mt-2 text-sm text-red-700 font-mono whitespace-pre-wrap">
                        {selectedStep.error_message}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div>
                <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Input Context Snapshot</h4>
                {selectedStep.input_data ? (
                  <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                    <pre className="text-[11px] text-green-400 font-mono">
                      {JSON.stringify(selectedStep.input_data, null, 2)}
                    </pre>
                  </div>
                ) : (
                  <p className="text-sm text-gray-400 italic">No input data captured yet.</p>
                )}
              </div>

              <div>
                <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Node Output</h4>
                {selectedStep.output_data ? (
                  <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                    <pre className="text-[11px] text-blue-400 font-mono">
                      {JSON.stringify(selectedStep.output_data, null, 2)}
                    </pre>
                  </div>
                ) : (
                  <p className="text-sm text-gray-400 italic">No output data generated yet.</p>
                )}
              </div>
              
              {selectedStep.duration_ms && (
                <div className="text-xs text-gray-500 flex justify-between border-t border-gray-100 pt-4">
                  <span>Execution Time</span>
                  <span className="font-mono font-bold text-gray-900">{selectedStep.duration_ms}ms</span>
                </div>
              )}

            </div>
          </div>
        )}
      </div>
    </div>
  );
};
