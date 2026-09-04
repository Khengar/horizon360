import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';
import {
  Zap, DollarSign, FolderKanban, Headphones, Users, ArrowRight,
  CheckCircle2, Clock, AlertCircle, RefreshCw, ChevronDown, ChevronUp,
  FileText, ListTodo, Ticket, UserCog
} from 'lucide-react';

/* ─── Types ─── */
interface OrchestrationDeal {
  deal_id: number;
  deal_title: string;
  deal_stage: string;
  orchestrated: boolean;
  finance: { invoices: any[] };
  projects: any[];
  service: { tickets: any[] };
  hrms: { activities: any[] };
}

/* ─── Constants ─── */
const BIOM_CONFIG: Record<string, { icon: any; color: string; bg: string; border: string; label: string }> = {
  Sales:    { icon: Zap,           color: 'text-blue-700',   bg: 'bg-blue-50',    border: 'border-blue-200',  label: 'Sales BIOM' },
  Finance:  { icon: DollarSign,    color: 'text-green-700',  bg: 'bg-green-50',   border: 'border-green-200', label: 'Finance BIOM' },
  Projects: { icon: FolderKanban,  color: 'text-purple-700', bg: 'bg-purple-50',  border: 'border-purple-200',label: 'Projects BIOM' },
  Service:  { icon: Headphones,    color: 'text-orange-700', bg: 'bg-orange-50',  border: 'border-orange-200',label: 'Service BIOM' },
  HRMS:     { icon: Users,         color: 'text-red-700',    bg: 'bg-red-50',     border: 'border-red-200',   label: 'HRMS BIOM' },
};

/* ─── Orchestration Flow Diagram ─── */
const OrchestrationFlowDiagram = () => (
  <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6 mb-6">
    <h2 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-5">
      Deal-Won Orchestration Flow — Automated Cross-BIOM Pipeline
    </h2>
    <div className="flex items-center justify-between gap-2">
      {/* Sales Trigger */}
      <div className={`flex flex-col items-center justify-center p-4 rounded-xl border ${BIOM_CONFIG.Sales.bg} ${BIOM_CONFIG.Sales.border} w-40 text-center`}>
        <Zap className={`w-6 h-6 mb-2 ${BIOM_CONFIG.Sales.color}`} />
        <div className={`text-xs font-bold ${BIOM_CONFIG.Sales.color}`}>Deal Won</div>
        <div className="text-[10px] text-gray-500 mt-1">Trigger Event</div>
      </div>

      <ArrowRight className="w-5 h-5 text-gray-300 shrink-0" />

      {/* Orchestration Engine */}
      <div className="flex flex-col items-center justify-center p-4 rounded-xl border border-gray-300 bg-gray-50 w-44 text-center">
        <RefreshCw className="w-6 h-6 mb-2 text-gray-600" />
        <div className="text-xs font-bold text-gray-700">Business Orchestrator</div>
        <div className="text-[10px] text-gray-400 mt-1">Automated Engine</div>
      </div>

      <ArrowRight className="w-5 h-5 text-gray-300 shrink-0" />

      {/* Target BIOMs */}
      <div className="flex gap-3">
        {(['Finance', 'Projects', 'Service', 'HRMS'] as const).map((biom) => {
          const cfg = BIOM_CONFIG[biom];
          const Icon = cfg.icon;
          return (
            <div key={biom} className={`flex flex-col items-center justify-center p-3 rounded-xl border ${cfg.bg} ${cfg.border} w-32 text-center`}>
              <Icon className={`w-5 h-5 mb-1.5 ${cfg.color}`} />
              <div className={`text-[11px] font-bold ${cfg.color}`}>{cfg.label}</div>
              <div className="text-[9px] text-gray-400 mt-1">
                {biom === 'Finance' && 'Invoice + GL'}
                {biom === 'Projects' && 'Project + Tasks'}
                {biom === 'Service' && 'Onboarding Ticket'}
                {biom === 'HRMS' && 'Resource Allocation'}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  </div>
);

/* ─── Won Deals List for Manual Trigger ─── */
const WonDealsPanel = ({ onOrchestrate, orchestratedDeals }: { onOrchestrate: (dealId: number) => void; orchestratedDeals: Set<number> }) => {
  const [deals, setDeals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    horizonApi.getDeals()
      .then(data => {
        const list = Array.isArray(data) ? data : data?.results || [];
        setDeals(list.filter((d: any) => d.stage === 'won'));
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-sm text-gray-400 py-4">Loading won deals...</div>;
  if (deals.length === 0) return <div className="text-sm text-gray-400 py-4">No won deals found. Close a deal from the Pipeline to trigger orchestration.</div>;

  return (
    <div className="space-y-2">
      {deals.map((deal) => (
        <div key={deal.id} className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-lg px-4 py-3">
          <div>
            <div className="text-sm font-semibold text-gray-900">{deal.title}</div>
            <div className="text-xs text-gray-500">
              ${parseFloat(deal.value).toLocaleString()} • Won {new Date(deal.updated_at || deal.created_at).toLocaleDateString()}
            </div>
          </div>
          {orchestratedDeals.has(deal.id) ? (
            <span className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-green-700 bg-green-50 border border-green-200 rounded-lg">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Orchestrated
            </span>
          ) : (
            <button
              onClick={() => onOrchestrate(deal.id)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-600 text-white text-xs font-medium rounded-lg hover:bg-brand-700 transition-colors"
            >
              <Zap className="w-3.5 h-3.5" />
              Orchestrate
            </button>
          )}
        </div>
      ))}
    </div>
  );
};

/* ─── Orchestration Detail Card ─── */
const OrchestrationDetailCard = ({ data, isExpanded, onToggle }: {
  data: OrchestrationDeal;
  isExpanded: boolean;
  onToggle: () => void;
}) => {
  const invoiceCount = data.finance?.invoices?.length || 0;
  const projectCount = data.projects?.length || 0;
  const ticketCount = data.service?.tickets?.length || 0;
  const activityCount = data.hrms?.activities?.length || 0;
  const totalActions = invoiceCount + projectCount + ticketCount + activityCount;

  const activeBioms = [
    invoiceCount > 0 && 'Finance',
    projectCount > 0 && 'Projects',
    ticketCount > 0 && 'Service',
    activityCount > 0 && 'HRMS',
  ].filter(Boolean) as string[];

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-green-100 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <div className="text-sm font-semibold text-gray-900">{data.deal_title}</div>
            <div className="text-xs text-gray-500">
              {totalActions} actions across {activeBioms.length} BIOMs
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex -space-x-1">
            {activeBioms.map((biom) => {
              const cfg = BIOM_CONFIG[biom];
              if (!cfg) return null;
              const Icon = cfg.icon;
              return (
                <div key={biom} className={`w-7 h-7 rounded-full ${cfg.bg} border-2 border-white flex items-center justify-center`}>
                  <Icon className={`w-3.5 h-3.5 ${cfg.color}`} />
                </div>
              );
            })}
          </div>
          {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
        </div>
      </button>

      {isExpanded && (
        <div className="px-5 pb-5 border-t border-gray-100">
          <div className="mt-4 space-y-3">
            {/* Finance */}
            {data.finance?.invoices?.map((inv: any) => (
              <div key={inv.id} className={`flex items-start gap-3 p-3 rounded-lg border ${BIOM_CONFIG.Finance.bg} ${BIOM_CONFIG.Finance.border}`}>
                <div className={`w-8 h-8 rounded-full bg-white flex items-center justify-center shrink-0 border ${BIOM_CONFIG.Finance.border}`}>
                  <FileText className={`w-4 h-4 ${BIOM_CONFIG.Finance.color}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold uppercase tracking-wider ${BIOM_CONFIG.Finance.color}`}>Finance</span>
                    <span className="text-[9px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-medium">INVOICE</span>
                  </div>
                  <div className="text-sm text-gray-700 mt-0.5">
                    {inv.invoice_number} — ${parseFloat(inv.amount).toLocaleString()} ({inv.status})
                  </div>
                </div>
              </div>
            ))}

            {/* Projects */}
            {data.projects?.map((proj: any) => (
              <div key={proj.id} className={`flex items-start gap-3 p-3 rounded-lg border ${BIOM_CONFIG.Projects.bg} ${BIOM_CONFIG.Projects.border}`}>
                <div className={`w-8 h-8 rounded-full bg-white flex items-center justify-center shrink-0 border ${BIOM_CONFIG.Projects.border}`}>
                  <ListTodo className={`w-4 h-4 ${BIOM_CONFIG.Projects.color}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold uppercase tracking-wider ${BIOM_CONFIG.Projects.color}`}>Projects</span>
                    <span className="text-[9px] bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded-full font-medium">PROJECT</span>
                  </div>
                  <div className="text-sm text-gray-700 mt-0.5">
                    {proj.name} — Status: {proj.status}
                  </div>
                </div>
              </div>
            ))}

            {/* Service */}
            {data.service?.tickets?.map((tkt: any) => (
              <div key={tkt.id} className={`flex items-start gap-3 p-3 rounded-lg border ${BIOM_CONFIG.Service.bg} ${BIOM_CONFIG.Service.border}`}>
                <div className={`w-8 h-8 rounded-full bg-white flex items-center justify-center shrink-0 border ${BIOM_CONFIG.Service.border}`}>
                  <Ticket className={`w-4 h-4 ${BIOM_CONFIG.Service.color}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold uppercase tracking-wider ${BIOM_CONFIG.Service.color}`}>Service</span>
                    <span className="text-[9px] bg-orange-100 text-orange-700 px-1.5 py-0.5 rounded-full font-medium">TICKET</span>
                  </div>
                  <div className="text-sm text-gray-700 mt-0.5">
                    {tkt.title} — Priority: {tkt.priority} ({tkt.status})
                  </div>
                </div>
              </div>
            ))}

            {/* HRMS */}
            {data.hrms?.activities?.map((act: any, idx: number) => (
              <div key={idx} className={`flex items-start gap-3 p-3 rounded-lg border ${BIOM_CONFIG.HRMS.bg} ${BIOM_CONFIG.HRMS.border}`}>
                <div className={`w-8 h-8 rounded-full bg-white flex items-center justify-center shrink-0 border ${BIOM_CONFIG.HRMS.border}`}>
                  <UserCog className={`w-4 h-4 ${BIOM_CONFIG.HRMS.color}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold uppercase tracking-wider ${BIOM_CONFIG.HRMS.color}`}>HRMS</span>
                    <span className="text-[9px] bg-red-100 text-red-700 px-1.5 py-0.5 rounded-full font-medium">ALLOCATION</span>
                  </div>
                  <div className="text-sm text-gray-700 mt-0.5">{act.title}</div>
                  <div className="text-xs text-gray-400 mt-0.5">{act.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

/* ─── Main Page ─── */
export const OrchestrationHub = () => {
  const [orchestrations, setOrchestrations] = useState<OrchestrationDeal[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(0);
  const [triggerResult, setTriggerResult] = useState<any>(null);
  const [triggering, setTriggering] = useState(false);
  const [orchestratedDeals, setOrchestratedDeals] = useState<Set<number>>(new Set());

  const fetchOrchestrations = async () => {
    try {
      // Get all won deals and their orchestration status
      const dealsData = await horizonApi.getDeals();
      const dealsList = Array.isArray(dealsData) ? dealsData : dealsData?.results || [];
      const wonDeals = dealsList.filter((d: any) => d.stage === 'won');

      const orchestrationResults: OrchestrationDeal[] = [];
      const orchestratedIds = new Set<number>();

      for (const deal of wonDeals) {
        try {
          const status = await horizonApi.getOrchestrationStatus(deal.id);
          if (status.orchestrated) {
            orchestrationResults.push(status);
            orchestratedIds.add(deal.id);
          }
        } catch {
          // Deal not orchestrated yet, skip
        }
      }

      setOrchestrations(orchestrationResults);
      setOrchestratedDeals(orchestratedIds);
    } catch (err) {
      console.error('Failed to load orchestrations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrchestrations();
  }, []);

  const handleOrchestrate = async (dealId: number) => {
    setTriggering(true);
    setTriggerResult(null);
    try {
      const res = await horizonApi.triggerOrchestration(dealId);
      setTriggerResult(res);
      // Refresh after a small delay to allow Celery task to complete
      setTimeout(() => fetchOrchestrations(), 2000);
    } catch (err: any) {
      setTriggerResult({ error: err?.response?.data?.error || 'Orchestration failed' });
    } finally {
      setTriggering(false);
    }
  };

  // Compute KPIs from orchestration data
  const totalInvoices = orchestrations.reduce((c, o) => c + (o.finance?.invoices?.length || 0), 0);
  const totalProjects = orchestrations.reduce((c, o) => c + (o.projects?.length || 0), 0);
  const totalTickets = orchestrations.reduce((c, o) => c + (o.service?.tickets?.length || 0), 0);
  const totalActivities = orchestrations.reduce((c, o) => c + (o.hrms?.activities?.length || 0), 0);

  return (
    <div className="flex-1 overflow-y-auto bg-[#f9fafb] h-full">
      {/* Header */}
      <header className="h-14 border-b border-gray-200 flex items-center justify-between px-8 bg-white shrink-0">
        <div>
          <h1 className="text-lg font-bold text-gray-900 leading-tight">Business Orchestration Hub</h1>
          <p className="text-[11px] text-gray-500">Automated Cross-BIOM Workflow Engine — Deal-to-Delivery Pipeline</p>
        </div>
        <button
          onClick={() => { setLoading(true); fetchOrchestrations(); }}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-brand-600 hover:bg-brand-700 text-white rounded-lg shadow-sm transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </header>

      <div className="p-8 max-w-7xl space-y-6">
        {/* Orchestration Flow Diagram */}
        <OrchestrationFlowDiagram />

        {/* KPI Stats */}
        <div className="grid grid-cols-5 gap-4">
          {[
            { label: 'Orchestrated Deals', value: orchestrations.length, accent: 'text-gray-900' },
            { label: 'Invoices Generated', value: totalInvoices, accent: 'text-green-700' },
            { label: 'Projects Created', value: totalProjects, accent: 'text-purple-700' },
            { label: 'Service Tickets', value: totalTickets, accent: 'text-orange-700' },
            { label: 'HR Allocations', value: totalActivities, accent: 'text-red-700' },
          ].map((stat) => (
            <div key={stat.label} className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="text-[11px] font-medium text-gray-500 uppercase tracking-wide mb-1">{stat.label}</div>
              <div className={`text-2xl font-bold ${stat.accent}`}>{stat.value}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* Left: Manual Trigger Panel */}
          <div className="col-span-1">
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
              <h3 className="text-sm font-bold text-gray-900 mb-1 flex items-center gap-2">
                <Zap className="w-4 h-4 text-brand-600" />
                Manual Orchestration
              </h3>
              <p className="text-[10px] text-gray-400 uppercase tracking-wider mb-4">
                Trigger for won deals
              </p>
              <WonDealsPanel onOrchestrate={handleOrchestrate} orchestratedDeals={orchestratedDeals} />

              {triggering && (
                <div className="mt-4 flex items-center gap-2 text-sm text-brand-600">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Running orchestration...
                </div>
              )}

              {triggerResult && !triggering && (
                <div className={`mt-4 p-3 rounded-lg text-sm ${triggerResult.error ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'}`}>
                  {triggerResult.error ? (
                    <div className="flex items-center gap-2">
                      <AlertCircle className="w-4 h-4" />
                      {triggerResult.error}
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" />
                      Orchestration triggered! Refreshing in 2s...
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Right: Orchestrated Deals */}
          <div className="col-span-2">
            <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3">
              Orchestrated Deals — Cross-BIOM Records
            </h3>
            {loading ? (
              <div className="text-sm text-gray-500 py-8 text-center">Loading orchestration history...</div>
            ) : orchestrations.length === 0 ? (
              <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
                <Zap className="w-8 h-8 text-gray-300 mx-auto mb-3" />
                <p className="text-sm text-gray-500">No orchestrations yet.</p>
                <p className="text-xs text-gray-400 mt-1">Mark a deal as "Won" in the Pipeline to trigger automated cross-BIOM orchestration.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {orchestrations.map((orch, idx) => (
                  <OrchestrationDetailCard
                    key={orch.deal_id}
                    data={orch}
                    isExpanded={expandedIdx === idx}
                    onToggle={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
