import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';
import { CheckCircle, XCircle, Clock, AlertTriangle, MessageSquare, Briefcase } from 'lucide-react';

export const Approvals = () => {
  const [approvals, setApprovals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'pending' | 'history'>('pending');
  const [selectedApproval, setSelectedApproval] = useState<any | null>(null);
  const [comment, setComment] = useState('');

  const fetchApprovals = async () => {
    try {
      setLoading(true);
      const data = await horizonApi.getV2Approvals();
      setApprovals(Array.isArray(data) ? data : data.results || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, []);

  const pendingApprovals = approvals.filter(a => a.status === 'pending');
  const historyApprovals = approvals.filter(a => a.status !== 'pending');

  const handleAction = async (id: string, action: 'approve' | 'reject') => {
    try {
      if (action === 'approve') {
        await horizonApi.approveV2Approval(id, comment);
      } else {
        await horizonApi.rejectV2Approval(id, comment);
      }
      setComment('');
      setSelectedApproval(null);
      fetchApprovals();
    } catch (e) {
      console.error('Action failed', e);
      alert('Failed to process approval.');
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-700 bg-red-100';
      case 'high': return 'text-orange-700 bg-orange-100';
      case 'medium': return 'text-blue-700 bg-blue-100';
      default: return 'text-gray-700 bg-gray-100';
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 flex-1">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-6">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">Approvals Inbox</h2>
            <p className="text-gray-500 mt-1">Manage human-in-the-loop tasks from automated workflows</p>
          </div>
          <div className="flex space-x-2">
             <div className="bg-indigo-50 text-indigo-700 px-4 py-2 rounded-lg font-bold flex items-center shadow-sm">
                <CheckCircle className="w-5 h-5 mr-2" />
                {pendingApprovals.length} Pending
             </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="max-w-6xl mx-auto mt-6 flex space-x-6 border-b border-gray-200">
          <button 
            className={`pb-3 font-medium text-sm border-b-2 transition-colors flex items-center ${activeTab === 'pending' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('pending')}
          >
            Action Required
            {pendingApprovals.length > 0 && (
              <span className="ml-2 bg-indigo-600 text-white px-2 py-0.5 rounded-full text-[10px] font-bold">
                {pendingApprovals.length}
              </span>
            )}
          </button>
          <button 
            className={`pb-3 font-medium text-sm border-b-2 transition-colors ${activeTab === 'history' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('history')}
          >
            History
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden flex max-w-6xl mx-auto w-full">
        {/* List Pane */}
        <div className="w-1/3 border-r border-gray-200 bg-white overflow-y-auto">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading inbox...</div>
          ) : (activeTab === 'pending' ? pendingApprovals : historyApprovals).length === 0 ? (
            <div className="p-8 text-center text-gray-500 flex flex-col items-center">
              <CheckCircle className="w-12 h-12 text-gray-300 mb-4" />
              <p>You're all caught up!</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {(activeTab === 'pending' ? pendingApprovals : historyApprovals).map(req => (
                <div 
                  key={req.id} 
                  onClick={() => setSelectedApproval(req)}
                  className={`p-5 cursor-pointer hover:bg-gray-50 transition-colors ${selectedApproval?.id === req.id ? 'bg-indigo-50 border-l-4 border-indigo-600' : 'border-l-4 border-transparent'}`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded ${getPriorityColor(req.priority)}`}>
                      {req.priority}
                    </span>
                    <span className="text-xs text-gray-400 flex items-center">
                      <Clock size={12} className="mr-1" />
                      {new Date(req.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <h4 className="font-bold text-gray-900 mb-1 line-clamp-2">{req.title}</h4>
                  <p className="text-xs text-gray-500 line-clamp-1">{req.description || 'No additional description provided.'}</p>
                  
                  {req.deadline && activeTab === 'pending' && (
                    <div className="mt-3 flex items-center text-xs text-red-600 bg-red-50 px-2 py-1 rounded inline-flex">
                      <AlertTriangle size={12} className="mr-1" />
                      Due: {new Date(req.deadline).toLocaleString()}
                    </div>
                  )}
                  {activeTab === 'history' && (
                    <div className="mt-2">
                      <span className={`text-xs font-bold ${req.status === 'approved' ? 'text-green-600' : 'text-red-600'}`}>
                        {req.status.toUpperCase()}
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detail Pane */}
        <div className="w-2/3 bg-gray-50 overflow-y-auto">
          {selectedApproval ? (
            <div className="p-8">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center space-x-2 mb-4">
                    <span className={`px-2 py-1 text-xs font-bold uppercase rounded ${getPriorityColor(selectedApproval.priority)}`}>
                      {selectedApproval.priority} Priority
                    </span>
                    <span className="text-sm text-gray-500 font-mono">ID: {selectedApproval.id.split('-')[0]}</span>
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">{selectedApproval.title}</h2>
                  <p className="text-gray-600">{selectedApproval.description}</p>
                </div>
                
                <div className="p-6 bg-gray-50 border-b border-gray-200">
                  <h4 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4 flex items-center">
                    <Briefcase size={16} className="mr-2 text-indigo-600" />
                    Workflow Context
                  </h4>
                  <div className="bg-white p-4 rounded border border-gray-200 overflow-x-auto">
                    <pre className="text-xs text-gray-700 font-mono">
                      {JSON.stringify(selectedApproval.context_data, null, 2)}
                    </pre>
                  </div>
                </div>

                {activeTab === 'pending' && (
                  <div className="p-6">
                    <h4 className="text-sm font-bold text-gray-900 mb-2 flex items-center">
                      <MessageSquare size={16} className="mr-2 text-gray-500" />
                      Approval Decision
                    </h4>
                    <textarea 
                      className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-indigo-500 focus:border-indigo-500 mb-4"
                      rows={3}
                      placeholder="Add an optional comment..."
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                    ></textarea>
                    
                    <div className="flex space-x-4">
                      <button 
                        onClick={() => handleAction(selectedApproval.id, 'approve')}
                        className="flex-1 bg-green-600 text-white font-bold py-3 rounded-lg hover:bg-green-700 flex items-center justify-center transition-colors shadow-sm"
                      >
                        <CheckCircle size={18} className="mr-2" />
                        Approve
                      </button>
                      <button 
                        onClick={() => handleAction(selectedApproval.id, 'reject')}
                        className="flex-1 bg-white border-2 border-red-200 text-red-600 font-bold py-3 rounded-lg hover:bg-red-50 flex items-center justify-center transition-colors"
                      >
                        <XCircle size={18} className="mr-2" />
                        Reject
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-gray-400 p-8 text-center">
              <CheckCircle size={48} className="mb-4 text-gray-300" />
              <h3 className="text-lg font-medium text-gray-600">No Item Selected</h3>
              <p className="mt-1">Select an approval request from the list to view details and take action.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
