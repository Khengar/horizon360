import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';
import { Link } from 'react-router-dom';

const STAGES = [
  { id: 'lead', label: 'Lead', color: 'bg-gray-100 border-gray-200 text-gray-800' },
  { id: 'qualified', label: 'Qualified', color: 'bg-blue-100 border-blue-200 text-blue-800' },
  { id: 'proposal', label: 'Proposal', color: 'bg-purple-100 border-purple-200 text-purple-800' },
  { id: 'negotiation', label: 'Negotiation', color: 'bg-orange-100 border-orange-200 text-orange-800' },
  { id: 'won', label: 'Won', color: 'bg-green-100 border-green-200 text-green-800' },
  { id: 'lost', label: 'Lost', color: 'bg-red-100 border-red-200 text-red-800' },
];

export const Pipeline = () => {
  const [deals, setDeals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [customers, setCustomers] = useState<any[]>([]);

  // Create Deal Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newDeal, setNewDeal] = useState({ title: '', value: 0, customer: '', stage: 'lead' });

  const fetchData = () => {
    setLoading(true);
    Promise.all([horizonApi.getDeals(), horizonApi.getCustomers()])
      .then(([dealsData, custData]) => {
        setDeals(dealsData);
        setCustomers(custData);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleStageChange = async (dealId: number, newStage: string) => {
    try {
      // Optimistic update
      setDeals(deals.map(d => d.id === dealId ? { ...d, stage: newStage } : d));
      await horizonApi.updateDeal(dealId, { stage: newStage });
      
      // Notify user when cross-BIOM orchestration is triggered
      if (newStage === 'won') {
        alert('🎉 Deal Won! Cross-BIOM Orchestration has been triggered automatically.\n\n• Finance: Invoice generated\n• Projects: Delivery project created\n• Service: Onboarding ticket opened\n• HRMS: Resource allocation requested\n\nView the Orchestration Hub for details.');
      }
    } catch (err) {
      console.error(err);
      alert('Failed to update stage.');
      fetchData(); // Revert
    }
  };

  const handleCreateDeal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDeal.title || !newDeal.customer) return alert('Title and Customer are required.');
    
    try {
      await horizonApi.createDeal({
        ...newDeal,
        value: Number(newDeal.value)
      });
      setShowCreateModal(false);
      setNewDeal({ title: '', value: 0, customer: '', stage: 'lead' });
      fetchData();
    } catch (err) {
      console.error(err);
      alert('Failed to create deal.');
    }
  };

  const getCustomerInfo = (customerId: string) => {
    return customers.find(c => c.id === customerId) || null;
  };

  if (loading) return <div className="p-8 text-gray-500">Loading Pipeline...</div>;

  return (
    <div className="flex-1 flex flex-col h-full bg-[#f9fafb] overflow-hidden">
      <header className="h-16 border-b border-gray-200 bg-white flex items-center justify-between px-8 shadow-sm shrink-0">
        <h1 className="text-xl font-bold text-gray-900">CRM Pipeline</h1>
        <button 
          onClick={() => setShowCreateModal(true)}
          className="bg-brand-600 text-white px-4 py-2 rounded-md font-medium text-sm hover:bg-brand-700 cursor-pointer"
        >
          + Create Deal
        </button>
      </header>

      <div className="flex-1 p-8 overflow-x-auto overflow-y-hidden">
        <div className="flex h-full gap-4 items-start pb-4" style={{ minWidth: 'min-content' }}>
          {STAGES.map(stage => {
            const stageDeals = deals.filter(d => d.stage === stage.id);
            const totalValue = stageDeals.reduce((sum, d) => sum + parseFloat(d.value), 0);

            return (
              <div key={stage.id} className="w-80 flex flex-col h-full bg-gray-50 rounded-lg border border-gray-200 shrink-0">
                <div className={`px-4 py-3 border-b border-gray-200 rounded-t-lg font-semibold flex justify-between items-center ${stage.color}`}>
                  <span>{stage.label}</span>
                  <span className="text-xs bg-white/50 px-2 py-0.5 rounded-full">${totalValue.toFixed(0)}</span>
                </div>
                
                <div className="flex-1 overflow-y-auto p-3 space-y-3">
                  {stageDeals.map(deal => {
                    const cust = getCustomerInfo(deal.customer);
                    return (
                      <div key={deal.id} className="bg-white p-3 rounded shadow-sm border border-gray-200 flex flex-col gap-2">
                        <div className="flex justify-between items-start">
                          <h4 className="font-semibold text-gray-900 text-sm leading-tight">{deal.title}</h4>
                          <span className="font-bold text-gray-700 text-sm">${parseFloat(deal.value).toFixed(0)}</span>
                        </div>
                        
                        <div className="text-xs text-gray-500">
                          {cust ? (
                            <Link to={`/customers/${cust.id}/360`} className="text-brand-600 hover:underline">
                              {cust.primary_email || cust.id.substring(0,8)}
                            </Link>
                          ) : (
                            'Unknown Customer'
                          )}
                        </div>

                        <div className="mt-2 flex justify-between items-center text-xs">
                           <span className="text-gray-400">{new Date(deal.created_at).toLocaleDateString()}</span>
                           <select 
                             value={deal.stage} 
                             onChange={(e) => handleStageChange(deal.id, e.target.value)}
                             className="border border-gray-200 rounded bg-gray-50 px-1 py-0.5 text-gray-600 outline-none"
                           >
                             {STAGES.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
                           </select>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex justify-center items-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <h2 className="text-xl font-bold mb-4">Create New Deal</h2>
            <form onSubmit={handleCreateDeal} className="flex flex-col gap-4">
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Deal Title *</label>
                <input required type="text" value={newDeal.title} onChange={e => setNewDeal({...newDeal, title: e.target.value})} className="w-full border border-gray-300 rounded px-3 py-2 outline-none focus:border-brand-500" placeholder="e.g. Enterprise License" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Customer *</label>
                <select required value={newDeal.customer} onChange={e => setNewDeal({...newDeal, customer: e.target.value})} className="w-full border border-gray-300 rounded px-3 py-2 outline-none focus:border-brand-500">
                  <option value="">Select a customer...</option>
                  {customers.map(c => (
                    <option key={c.id} value={c.id}>{c.primary_email || c.id}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Value ($)</label>
                <input required type="number" min="0" step="0.01" value={newDeal.value} onChange={e => setNewDeal({...newDeal, value: Number(e.target.value)})} className="w-full border border-gray-300 rounded px-3 py-2 outline-none focus:border-brand-500" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Stage</label>
                <select value={newDeal.stage} onChange={e => setNewDeal({...newDeal, stage: e.target.value})} className="w-full border border-gray-300 rounded px-3 py-2 outline-none focus:border-brand-500">
                  {STAGES.map(s => (
                    <option key={s.id} value={s.id}>{s.label}</option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end gap-3 mt-4">
                <button type="button" onClick={() => setShowCreateModal(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-brand-600 text-white rounded hover:bg-brand-700">Create Deal</button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
