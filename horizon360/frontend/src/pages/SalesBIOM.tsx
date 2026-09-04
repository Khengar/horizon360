import React, { useEffect, useState, useRef } from 'react';
import { horizonApi } from '../api';
import { Link } from 'react-router-dom';
import {
  TrendingUp, Zap, Radio, Filter, Plus, CheckCircle2, XCircle,
  RefreshCw, Terminal, Eye, ArrowRight, UserCheck, DollarSign,
  Clock, Shield, Award, Play, Pause, ChevronRight
} from 'lucide-react';

/* ─── Stage Definitions (PPT Level 4 Sales Workflow) ─── */
const PIPELINE_STAGES = [
  { id: 'visitor',     label: 'Visitor',     badge: 'bg-slate-100 text-slate-700 border-slate-200',  accent: 'border-t-slate-400',  prob: 5,   desc: 'Anonymous Ingestion & Web Traffic' },
  { id: 'lead',        label: 'Lead',        badge: 'bg-blue-100 text-blue-700 border-blue-200',    accent: 'border-t-blue-500',   prob: 25,  desc: 'Scored Inbound & SDR Qualified' },
  { id: 'opportunity', label: 'Opportunity', badge: 'bg-purple-100 text-purple-700 border-purple-200',accent: 'border-t-purple-500', prob: 50,  desc: 'Accepted Enterprise Deal' },
  { id: 'proposal',    label: 'Proposal',    badge: 'bg-amber-100 text-amber-700 border-amber-200',  accent: 'border-t-amber-500',  prob: 75,  desc: 'CPQ Quote & Contract Sent' },
  { id: 'won',         label: 'Won',         badge: 'bg-emerald-100 text-emerald-700 border-emerald-200',accent: 'border-t-emerald-500',prob: 100, desc: 'Closed-Won (Auto Orchestration)' },
  { id: 'lost',        label: 'Lost',        badge: 'bg-rose-100 text-rose-700 border-rose-200',    accent: 'border-t-rose-400',   prob: 0,   desc: 'Closed-Lost Opportunity' },
];

/* ─── Kafka Event Model ─── */
interface KafkaEvent {
  offset: number;
  partition: number;
  topic: string;
  key: string;
  eventName: string;
  timestamp: string;
  payload: Record<string, any>;
  highlight?: boolean;
}

export const SalesBIOM = () => {
  const [deals, setDeals] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'kanban' | 'kafka' | 'split'>('split');
  const [isKafkaStreaming, setIsKafkaStreaming] = useState(true);

  // Kafka log stream state
  const [kafkaEvents, setKafkaEvents] = useState<KafkaEvent[]>([]);
  const kafkaOffsetCounter = useRef(104820);
  const eventStreamEndRef = useRef<HTMLDivElement>(null);

  // Modal State for New Deal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newDeal, setNewDeal] = useState({
    title: '',
    value: 5000,
    customer: '',
    stage: 'visitor',
  });

  /* ─── Load Live Data ─── */
  const fetchData = async () => {
    setLoading(true);
    try {
      const [dealsData, custData, eventsData] = await Promise.all([
        horizonApi.getDeals(),
        horizonApi.getCustomers(),
        horizonApi.getEvents().catch(() => []),
      ]);

      const dealList = Array.isArray(dealsData) ? dealsData : dealsData?.results || [];
      const custList = Array.isArray(custData) ? custData : custData?.results || [];

      // Normalize deal stages to standard PPT workflow
      const normalizedDeals = dealList.map((d: any) => {
        let stage = d.stage;
        if (stage === 'qualified') stage = 'opportunity';
        if (stage === 'negotiation') stage = 'proposal';
        return { ...d, stage };
      });

      setDeals(normalizedDeals);
      setCustomers(custList);

      // Seed initial Kafka events from RawEvents or mock stream
      const rawList = Array.isArray(eventsData) ? eventsData : eventsData?.results || [];
      const initialKafka: KafkaEvent[] = rawList.slice(0, 15).map((ev: any, idx: number) => ({
        offset: kafkaOffsetCounter.current + idx,
        partition: idx % 3,
        topic: 'domain.events.sales',
        key: String(ev.customer || ev.id || 'cust_key'),
        eventName: ev.event_name || 'sales.activity.tracked',
        timestamp: ev.created_at || new Date().toISOString(),
        payload: ev.raw_payload || { event: ev.event_name, id: ev.id },
      }));

      if (initialKafka.length === 0) {
        // Fallback demo events
        initialKafka.push(
          {
            offset: kafkaOffsetCounter.current++,
            partition: 0,
            topic: 'domain.events.sales',
            key: 'usr_84920',
            eventName: 'visitor.identified',
            timestamp: new Date(Date.now() - 120000).toISOString(),
            payload: { ip: '198.51.100.42', referrer: 'google/search', page: '/pricing', intent_score: 0.82 },
          },
          {
            offset: kafkaOffsetCounter.current++,
            partition: 1,
            topic: 'domain.events.sales',
            key: 'cust_3910',
            eventName: 'lead.captured',
            timestamp: new Date(Date.now() - 60000).toISOString(),
            payload: { email: 'enterprise@cyberdyne.io', source: 'demo_request', tier: 'enterprise' },
          }
        );
      }

      setKafkaEvents(initialKafka.reverse());
    } catch (err) {
      console.error('Failed to load Sales BIOM data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  /* ─── Emit a Kafka Event Helper ─── */
  const emitKafkaEvent = (eventName: string, key: string, payload: Record<string, any>) => {
    const newOffset = ++kafkaOffsetCounter.current;
    const newEvent: KafkaEvent = {
      offset: newOffset,
      partition: Math.floor(Math.random() * 3),
      topic: 'domain.events.sales',
      key,
      eventName,
      timestamp: new Date().toISOString(),
      payload,
      highlight: true,
    };

    setKafkaEvents((prev) => [newEvent, ...prev.slice(0, 49)]);
  };

  /* ─── Stage Change Handler ─── */
  const handleStageChange = async (dealId: number, targetStage: string) => {
    const deal = deals.find((d) => d.id === dealId);
    if (!deal) return;

    const oldStage = deal.stage;

    // Optimistic UI Update
    setDeals((prev) =>
      prev.map((d) => (d.id === dealId ? { ...d, stage: targetStage } : d))
    );

    // Emit live event to Kafka stream
    emitKafkaEvent(`sales.stage_transition`, `deal_${dealId}`, {
      deal_id: dealId,
      deal_title: deal.title,
      from_stage: oldStage,
      to_stage: targetStage,
      deal_value: parseFloat(deal.value),
      emitted_by: 'SalesBIOM_Kanban',
    });

    try {
      await horizonApi.updateDeal(dealId, { stage: targetStage });

      // If moved to 'won', also notify and trigger orchestration
      if (targetStage === 'won') {
        emitKafkaEvent(`sales.deal_won.orchestrate`, `deal_${dealId}`, {
          deal_id: dealId,
          deal_title: deal.title,
          deal_value: parseFloat(deal.value),
          action: 'cross_biom_cascade_initiated',
          downstream_targets: ['Finance', 'Projects', 'Service', 'HRMS'],
        });

        alert(
          `🎉 Deal Won! [${deal.title}]\n\nKafka event 'sales.deal_won.orchestrate' published.\nAutomated Business Orchestration triggered across Finance, Projects, Service, and HRMS!`
        );
      }
    } catch (err) {
      console.error('Failed to update stage:', err);
      fetchData(); // revert
    }
  };

  /* ─── Create Deal Handler ─── */
  const handleCreateDeal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDeal.title || !newDeal.customer) {
      return alert('Deal Title and Customer are required.');
    }

    try {
      const created = await horizonApi.createDeal({
        ...newDeal,
        value: Number(newDeal.value),
      });

      emitKafkaEvent(`sales.${newDeal.stage}.created`, `deal_${created.id}`, {
        deal_id: created.id,
        title: newDeal.title,
        stage: newDeal.stage,
        value: Number(newDeal.value),
        customer_id: newDeal.customer,
      });

      setShowCreateModal(false);
      setNewDeal({ title: '', value: 5000, customer: '', stage: 'visitor' });
      fetchData();
    } catch (err) {
      console.error('Failed to create deal:', err);
      alert('Error creating deal.');
    }
  };

  // Helper metrics
  const totalPipeline = deals
    .filter((d) => d.stage !== 'lost')
    .reduce((sum, d) => sum + (parseFloat(d.value) || 0), 0);
  const wonRevenue = deals
    .filter((d) => d.stage === 'won')
    .reduce((sum, d) => sum + (parseFloat(d.value) || 0), 0);
  const activeCount = deals.filter((d) => d.stage !== 'won' && d.stage !== 'lost').length;
  const wonCount = deals.filter((d) => d.stage === 'won').length;
  const winRate = deals.length > 0 ? Math.round((wonCount / deals.length) * 100) : 0;

  return (
    <div className="flex-1 flex flex-col h-full bg-[#f8fafc] overflow-hidden">
      {/* ─── Header ─── */}
      <header className="h-16 border-b border-gray-200 bg-white flex items-center justify-between px-8 shrink-0 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-blue-600 text-white flex items-center justify-center shadow-sm">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-gray-900 leading-tight">Sales BIOM</h1>
              <span className="text-[10px] bg-blue-100 text-blue-800 font-semibold px-2 py-0.5 rounded-full">
                Level 4 BIOM
              </span>
            </div>
            <p className="text-xs text-gray-500">
              Visitor ➔ Lead ➔ Opportunity ➔ Proposal ➔ Won/Loss • Enterprise Event Stream
            </p>
          </div>
        </div>

        {/* View Switcher & Action Controls */}
        <div className="flex items-center gap-3">
          <div className="bg-gray-100 p-0.5 rounded-lg flex items-center border border-gray-200 text-xs font-medium">
            <button
              onClick={() => setViewMode('kanban')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                viewMode === 'kanban'
                  ? 'bg-white text-gray-900 shadow-sm font-semibold'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Kanban
            </button>
            <button
              onClick={() => setViewMode('split')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                viewMode === 'split'
                  ? 'bg-white text-gray-900 shadow-sm font-semibold'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Split View
            </button>
            <button
              onClick={() => setViewMode('kafka')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                viewMode === 'kafka'
                  ? 'bg-white text-gray-900 shadow-sm font-semibold'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Kafka Stream
            </button>
          </div>

          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-medium shadow-sm transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" /> Add Item
          </button>
        </div>
      </header>

      {/* ─── Metric KPI Bar ─── */}
      <div className="bg-white border-b border-gray-200 px-8 py-3 grid grid-cols-5 gap-4 shrink-0">
        <div>
          <div className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider">Total Pipeline</div>
          <div className="text-lg font-bold text-gray-900">${totalPipeline.toLocaleString()}</div>
        </div>
        <div>
          <div className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider">Active Deals</div>
          <div className="text-lg font-bold text-blue-600">{activeCount} In Flight</div>
        </div>
        <div>
          <div className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider">Won Revenue</div>
          <div className="text-lg font-bold text-emerald-600">${wonRevenue.toLocaleString()}</div>
        </div>
        <div>
          <div className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider">Win Rate</div>
          <div className="text-lg font-bold text-purple-600">{winRate}%</div>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider">Kafka Broker</div>
            <div className="text-xs font-semibold text-emerald-600 flex items-center gap-1.5 mt-0.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Connected (3 Partitions)
            </div>
          </div>
          <button
            onClick={fetchData}
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Refresh Data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* ─── Main Content Canvas ─── */}
      <div className="flex-1 overflow-hidden flex">
        {/* ═══ 1. KANBAN PIPELINE VIEW ═══ */}
        {(viewMode === 'kanban' || viewMode === 'split') && (
          <div className={`flex-1 overflow-x-auto overflow-y-hidden p-6 ${viewMode === 'split' ? 'border-r border-gray-200' : ''}`}>
            <div className="flex h-full gap-4 items-start pb-2" style={{ minWidth: 'min-content' }}>
              {PIPELINE_STAGES.map((stage) => {
                const stageDeals = deals.filter((d) => d.stage === stage.id);
                const stageSum = stageDeals.reduce((sum, d) => sum + (parseFloat(d.value) || 0), 0);

                return (
                  <div
                    key={stage.id}
                    className={`w-72 flex flex-col h-full bg-gray-50/80 rounded-xl border border-gray-200 shadow-xs shrink-0 border-t-4 ${stage.accent}`}
                  >
                    {/* Column Header */}
                    <div className="p-3 border-b border-gray-200/80 bg-white/70 rounded-t-lg">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-bold text-xs text-gray-900 flex items-center gap-1.5">
                          {stage.label}
                          <span className="text-[10px] font-normal px-1.5 py-0.2 bg-gray-100 text-gray-600 rounded-full">
                            {stageDeals.length}
                          </span>
                        </span>
                        <span className="text-xs font-semibold text-gray-700">
                          ${stageSum.toLocaleString()}
                        </span>
                      </div>
                      <p className="text-[10px] text-gray-400 leading-tight">{stage.desc}</p>
                    </div>

                    {/* Cards Container */}
                    <div className="flex-1 overflow-y-auto p-2.5 space-y-2.5">
                      {stageDeals.length === 0 ? (
                        <div className="h-28 border-2 border-dashed border-gray-200 rounded-lg flex items-center justify-center text-center p-3">
                          <p className="text-xs text-gray-400">No deals in {stage.label}</p>
                        </div>
                      ) : (
                        stageDeals.map((deal) => {
                          const cust = customers.find((c) => c.id === deal.customer);
                          return (
                            <div
                              key={deal.id}
                              className="bg-white p-3.5 rounded-lg border border-gray-200/90 shadow-xs hover:shadow-md transition-shadow flex flex-col gap-2 relative group"
                            >
                              <div className="flex justify-between items-start gap-2">
                                <h4 className="font-semibold text-gray-900 text-xs leading-snug hover:text-blue-600 transition-colors">
                                  {deal.title}
                                </h4>
                                <span className="font-bold text-xs text-gray-900 shrink-0">
                                  ${parseFloat(deal.value || 0).toLocaleString()}
                                </span>
                              </div>

                              <div className="text-[11px] text-gray-500 flex items-center gap-1">
                                <span className="text-gray-400">Contact:</span>
                                {cust ? (
                                  <Link
                                    to={`/crm/customers/${cust.id}`}
                                    className="text-blue-600 hover:underline truncate max-w-[140px]"
                                  >
                                    {cust.primary_email || cust.id.slice(0, 8)}
                                  </Link>
                                ) : (
                                  <span className="text-gray-400 italic">Unassigned</span>
                                )}
                              </div>

                              {/* Stage Mover Controls */}
                              <div className="pt-2 mt-1 border-t border-gray-100 flex items-center justify-between">
                                <span className="text-[10px] text-gray-400 font-mono">
                                  ID: {deal.id}
                                </span>
                                <div className="flex items-center gap-1">
                                  <span className="text-[10px] text-gray-400">Move:</span>
                                  <select
                                    value={deal.stage}
                                    onChange={(e) => handleStageChange(deal.id, e.target.value)}
                                    className="text-[11px] font-medium bg-gray-50 border border-gray-200 rounded px-1.5 py-0.5 text-gray-700 outline-none focus:border-blue-500 cursor-pointer"
                                  >
                                    {PIPELINE_STAGES.map((s) => (
                                      <option key={s.id} value={s.id}>
                                        {s.label}
                                      </option>
                                    ))}
                                  </select>
                                </div>
                              </div>
                            </div>
                          );
                        })
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ═══ 2. KAFKA EVENT STREAM DISPLAY ═══ */}
        {(viewMode === 'kafka' || viewMode === 'split') && (
          <div
            className={`flex flex-col bg-[#0f172a] text-slate-100 shrink-0 ${
              viewMode === 'split' ? 'w-[440px]' : 'flex-1'
            }`}
          >
            {/* Terminal Header */}
            <div className="h-10 px-4 bg-[#1e293b] border-b border-slate-700 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-emerald-400" />
                <span className="font-mono font-semibold text-slate-200">
                  Kafka Topic: domain.events.sales
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                  LIVE
                </span>
                <button
                  onClick={() =>
                    emitKafkaEvent('visitor.pageview', 'usr_anon', {
                      url: '/solutions/enterprise',
                      dwell_time_sec: 45,
                      source: 'organic_search',
                    })
                  }
                  className="px-2 py-0.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded text-[10px] font-mono cursor-pointer"
                  title="Simulate Inbound Visitor Event"
                >
                  + Ping Visitor
                </button>
              </div>
            </div>

            {/* Event Stream Log */}
            <div className="flex-1 overflow-y-auto p-3 font-mono text-xs space-y-2.5">
              {kafkaEvents.length === 0 ? (
                <div className="text-slate-500 text-center py-10">No Kafka events received yet.</div>
              ) : (
                kafkaEvents.map((ev, idx) => {
                  const isWonEvent = ev.eventName.includes('won');
                  return (
                    <div
                      key={idx}
                      className={`p-2.5 rounded-lg border transition-all ${
                        isWonEvent
                          ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-200'
                          : ev.highlight
                          ? 'bg-blue-950/40 border-blue-500/50 text-blue-200'
                          : 'bg-slate-900/90 border-slate-800 text-slate-300'
                      }`}
                    >
                      <div className="flex justify-between items-start text-[11px] mb-1">
                        <span className="font-bold text-amber-400 truncate max-w-[200px]">
                          {ev.eventName}
                        </span>
                        <span className="text-[10px] text-slate-500">
                          {new Date(ev.timestamp).toLocaleTimeString()}
                        </span>
                      </div>

                      <div className="flex items-center gap-3 text-[10px] text-slate-400 mb-1.5">
                        <span>P:{ev.partition}</span>
                        <span>Off:{ev.offset}</span>
                        <span className="truncate">Key:{ev.key}</span>
                      </div>

                      <div className="bg-black/40 p-2 rounded border border-slate-800/80 overflow-x-auto text-[11px] text-emerald-300">
                        <pre className="whitespace-pre-wrap leading-relaxed">
                          {JSON.stringify(ev.payload, null, 2)}
                        </pre>
                      </div>
                    </div>
                  );
                })
              )}
              <div ref={eventStreamEndRef} />
            </div>

            {/* Terminal Footer */}
            <div className="p-2.5 bg-[#1e293b] border-t border-slate-700 text-[10px] text-slate-400 flex justify-between items-center font-mono">
              <span>Consumer Group: sales_biom_engine</span>
              <span>Events In Buffer: {kafkaEvents.length}</span>
            </div>
          </div>
        )}
      </div>

      {/* ─── Modal: Create New Item (Visitor / Lead / Opportunity) ─── */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-xs flex justify-center items-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <h2 className="text-base font-bold text-gray-900 mb-1">Add Sales Pipeline Item</h2>
            <p className="text-xs text-gray-500 mb-4">
              Add a record into the Level 4 Sales BIOM pipeline. Emits an event to Kafka on creation.
            </p>

            <form onSubmit={handleCreateDeal} className="flex flex-col gap-3.5">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Stage *</label>
                <select
                  value={newDeal.stage}
                  onChange={(e) => setNewDeal({ ...newDeal, stage: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500"
                >
                  {PIPELINE_STAGES.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.label} — {s.desc}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Title / Company Name *</label>
                <input
                  required
                  type="text"
                  value={newDeal.title}
                  onChange={(e) => setNewDeal({ ...newDeal, title: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500"
                  placeholder="e.g. Wayne Enterprises Cloud Contract"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Customer Contact *</label>
                <select
                  required
                  value={newDeal.customer}
                  onChange={(e) => setNewDeal({ ...newDeal, customer: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500"
                >
                  <option value="">Select customer...</option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.primary_email || c.id}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Estimated Value ($)</label>
                <input
                  required
                  type="number"
                  min="0"
                  step="100"
                  value={newDeal.value}
                  onChange={(e) => setNewDeal({ ...newDeal, value: Number(e.target.value) })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex justify-end gap-2.5 mt-3 pt-3 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3.5 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition-colors cursor-pointer"
                >
                  Create & Emit to Kafka
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
