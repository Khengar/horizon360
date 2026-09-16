import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  ArrowRight
} from 'lucide-react';

// ─── Sub-components ───

const PipelineStage = ({ label, count, color, text, isLast }: { label: string, count: number | string, color: string, text: string, isLast?: boolean }) => (
  <div className="flex flex-col md:flex-row items-center w-full md:w-auto flex-1">
    <div className={`w-full min-w-[140px] rounded-xl border p-5 ${color} ${text} shadow-sm flex flex-col items-center justify-center text-center transition-all hover:-translate-y-1`}>
      <span className="text-sm font-semibold opacity-90 mb-1 tracking-wide uppercase">{label}</span>
      <span className="text-3xl font-bold">{count}</span>
    </div>
    {!isLast && (
      <div className="flex md:hidden py-2 text-gray-300">
        <ArrowRight className="w-5 h-5 rotate-90" />
      </div>
    )}
    {!isLast && (
      <div className="hidden md:flex px-3 text-gray-300">
        <ArrowRight className="w-6 h-6" />
      </div>
    )}
  </div>
);

const ActivityList = ({ title, deals, customers, stageIds }: { title: string, deals: any[], customers: any[], stageIds: string[] }) => {
  const filteredDeals = deals.filter(d => stageIds.includes(d.stage));
  
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden flex flex-col h-[350px]">
      <div className="bg-gray-50 border-b border-gray-200 px-4 py-3 flex justify-between items-center shrink-0">
        <h3 className="font-semibold text-gray-900 text-sm">{title}</h3>
        <span className="text-xs font-semibold bg-white border border-gray-200 text-gray-600 px-2 py-0.5 rounded-full shadow-xs">
          Total: {filteredDeals.length}
        </span>
      </div>
      <div className="p-4 flex-1 overflow-y-auto space-y-3">
        {filteredDeals.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-400">
            <span className="text-sm">No records</span>
          </div>
        ) : (
          filteredDeals.map(deal => {
            const cust = customers.find(c => c.id === deal.customer);
            return (
              <div key={deal.id} className="border border-gray-100 rounded-lg p-3 bg-gray-50 hover:bg-white transition-colors">
                <div className="flex justify-between items-start mb-1.5">
                  <span className="text-xs font-semibold text-gray-900 line-clamp-2 pr-2">{deal.title || 'Untitled Activity'}</span>
                  <span className="text-xs font-bold text-gray-700 shrink-0">${parseFloat(deal.value || 0).toLocaleString()}</span>
                </div>
                <div className="text-[11px] text-gray-500 flex flex-col gap-1">
                  <div className="flex items-center gap-1">
                    <span className="text-gray-400">Contact:</span>
                    {cust ? (
                      <Link to={`/crm/customers/${cust.id}`} className="text-blue-600 hover:underline truncate">
                        {cust.primary_email || cust.id.slice(0, 8)}
                      </Link>
                    ) : (
                      <span className="text-gray-400 italic">Unassigned</span>
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-gray-400">ID:</span>
                    <span className="font-mono">{deal.id}</span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

// ─── Data Definitions ───

const PIPELINE_STAGES = [
  { id: 'visitor', label: 'Visitor', color: 'bg-blue-50 border-blue-200', text: 'text-blue-800' },
  { id: 'lead', label: 'Lead', color: 'bg-blue-200 border-blue-300', text: 'text-blue-900' },
  { id: 'opportunity', label: 'Opportunity', color: 'bg-blue-400 border-blue-500', text: 'text-white' },
  { id: 'proposal', label: 'Proposal', color: 'bg-blue-600 border-blue-700', text: 'text-white' },
  { id: 'won_loss', label: 'Won/Loss', color: 'bg-blue-800 border-blue-900', text: 'text-white' },
];

// ─── Main Component ───

export const SalesBIOM = () => {
  const [deals, setDeals] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dealsData, custData] = await Promise.all([
        horizonApi.getDeals(),
        horizonApi.getCustomers(),
      ]);
      
      const dealList = Array.isArray(dealsData) ? dealsData : dealsData?.results || [];
      const custList = Array.isArray(custData) ? custData : custData?.results || [];

      // Normalize deal stages
      const normalizedDeals = dealList.map((d: any) => {
        let stage = d.stage;
        if (stage === 'qualified') stage = 'opportunity';
        if (stage === 'negotiation') stage = 'proposal';
        return { ...d, stage };
      });

      setDeals(normalizedDeals);
      setCustomers(custList);
    } catch (err) {
      console.error('Failed to load Sales BIOM data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getStageCount = (stageId: string) => {
    if (loading) return '-';
    if (stageId === 'won_loss') {
      return deals.filter(d => d.stage === 'won' || d.stage === 'lost').length;
    }
    return deals.filter(d => d.stage === stageId).length;
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-white overflow-y-auto">
      {/* ─── Header ─── */}
      <header className="py-8 px-8 border-b border-gray-100 bg-white flex flex-col items-start shrink-0">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-sm">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-2xl font-bold text-gray-900 leading-tight">Sales BIOM</h1>
              <span className="text-xs bg-blue-50 border border-blue-200 text-blue-700 font-semibold px-2.5 py-1 rounded-full">
                Level 4 BIOM
              </span>
            </div>
            <p className="text-sm text-gray-500 font-medium">
              Convert opportunities into revenue
            </p>
          </div>
        </div>
      </header>

      <main className="p-8 max-w-7xl mx-auto w-full flex flex-col gap-12">
        {/* ─── Horizontal Pipeline ─── */}
        <section>
          <div className="mb-6">
            <h2 className="text-lg font-bold text-gray-900 mb-1">Pipeline Overview</h2>
            <p className="text-sm text-gray-500">Live opportunity flow across standard stages</p>
          </div>
          
          <div className="flex flex-col md:flex-row items-stretch md:items-center w-full bg-white">
            {PIPELINE_STAGES.map((stage, idx) => (
              <PipelineStage
                key={stage.id}
                label={stage.label}
                count={getStageCount(stage.id)}
                color={stage.color}
                text={stage.text}
                isLast={idx === PIPELINE_STAGES.length - 1}
              />
            ))}
          </div>
        </section>

        {/* ─── Activity / Data Boxes ─── */}
        <section>
          <div className="mb-6">
            <h2 className="text-lg font-bold text-gray-900 mb-1">Pipeline Activities & Records</h2>
            <p className="text-sm text-gray-500">Real-time data synchronization from core services</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-5">
            <ActivityList title="All Visitors" deals={deals} customers={customers} stageIds={['visitor']} />
            <ActivityList title="All Leads" deals={deals} customers={customers} stageIds={['lead']} />
            <ActivityList title="All Opportunities" deals={deals} customers={customers} stageIds={['opportunity']} />
            <ActivityList title="All Proposals" deals={deals} customers={customers} stageIds={['proposal']} />
            <ActivityList title="Won/Loss" deals={deals} customers={customers} stageIds={['won', 'lost']} />
          </div>
        </section>
      </main>
    </div>
  );
};
