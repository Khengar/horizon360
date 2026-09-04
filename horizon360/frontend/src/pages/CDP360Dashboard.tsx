import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';
import { Database, UserCheck, GitMerge, Zap, Brain, RefreshCw, Activity, Shield, Target, Radio, Check, X } from 'lucide-react';

/* ───────────────────── Helper Components ───────────────────── */

const PhaseCard = ({ name, icon: Icon, metric, progress, theme }: {
  name: string; icon: any; metric: string; progress: number; theme: string;
}) => {
  const themeMap: Record<string, { bg: string; text: string; border: string; bar: string }> = {
    green:  { bg: 'bg-green-50',  text: 'text-green-700',  border: 'border-green-200',  bar: 'bg-green-500' },
    blue:   { bg: 'bg-blue-50',   text: 'text-blue-700',   border: 'border-blue-200',   bar: 'bg-blue-500' },
    purple: { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200', bar: 'bg-purple-500' },
    orange: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200', bar: 'bg-orange-500' },
    red:    { bg: 'bg-red-50',    text: 'text-red-700',    border: 'border-red-200',    bar: 'bg-red-500' },
  };
  const t = themeMap[theme] || themeMap.green;

  return (
    <div className={`flex flex-col items-center justify-center p-4 rounded-xl border ${t.bg} ${t.text} ${t.border} w-44 text-center relative`}>
      <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-green-500" title="Active" />
      <Icon className="w-6 h-6 mb-2 opacity-80" />
      <div className="text-xs font-bold mb-1 leading-tight">{name}</div>
      <div className="text-[11px] opacity-80 font-medium">{metric}</div>
      <div className="mt-2 w-full bg-white/60 rounded-full h-1.5">
        <div className={`${t.bar} h-1.5 rounded-full transition-all`} style={{ width: `${Math.min(progress, 100)}%` }} />
      </div>
      <div className="text-[10px] mt-1 opacity-60 uppercase tracking-wide">Active ✓</div>
    </div>
  );
};

const Arrow = () => (
  <div className="flex items-center text-gray-300 text-2xl font-light select-none px-1">→</div>
);

const KpiCard = ({ title, value, accent }: { title: string; value: string | number; accent?: string }) => (
  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
    <div className="text-[11px] font-medium text-gray-500 uppercase tracking-wide mb-1">{title}</div>
    <div className={`text-2xl font-bold ${accent || 'text-gray-900'}`}>{typeof value === 'number' ? value.toLocaleString() : value}</div>
  </div>
);

const FeatureCard = ({ emoji, title, subtitle, children }: {
  emoji: string; title: string; subtitle: string; children: React.ReactNode;
}) => (
  <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5 flex flex-col">
    <div className="flex items-center gap-2 mb-1">
      <span className="text-lg">{emoji}</span>
      <h3 className="text-sm font-bold text-gray-800">{title}</h3>
    </div>
    <p className="text-[10px] text-gray-400 uppercase tracking-wider mb-3">{subtitle}</p>
    <div className="flex-1">{children}</div>
  </div>
);

/* ───────────────────── Main Dashboard ───────────────────── */

export const CDP360Dashboard = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const result = await horizonApi.getCDPPipeline();
      setData(result);
    } catch (err) {
      console.error('Failed to load CDP pipeline data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleRefresh = () => { setRefreshing(true); loadData(); };

  const handleApproveMerge = async (id: string) => {
    try { await horizonApi.approveMergeSuggestion(id); loadData(); }
    catch (err) { console.error('Merge approval failed:', err); }
  };

  const handleRejectMerge = async (id: string) => {
    try { await horizonApi.rejectMergeSuggestion(id); loadData(); }
    catch (err) { console.error('Merge rejection failed:', err); }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center h-full bg-white">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500 text-sm">Loading CDP 360 Pipeline…</p>
        </div>
      </div>
    );
  }

  // ─── Extract data from API response ───
  const pipeline    = data?.pipeline || {};
  const rawData     = pipeline.raw_data || {};
  const identity    = pipeline.identity_resolution || {};
  const unification = pipeline.data_unification || {};
  const enrichment  = pipeline.profile_enrichment || {};
  const intelligence = pipeline.intelligence || {};

  const features    = data?.features || {};
  const eventTracking = features.event_tracking || {};
  const segmentation  = features.segmentation || {};
  const consent       = features.consent || {};

  const mergeSuggestions = data?.merge_suggestions || [];
  const recentEvents     = eventTracking.recent_events || [];

  // Compute progress percentages
  const totalEvents   = rawData.total_events || 0;
  const processed     = identity.deterministic_matches || 0;
  const unifiedCount  = unification.unified_profiles || 0;
  const enrichedCount = enrichment.enriched_profiles || 0;
  const segmentsCount = intelligence.active_segments || 0;

  const identityPct    = totalEvents > 0 ? Math.round((processed / totalEvents) * 100) : 0;
  const unificationPct = (identity.profiles_created || 1) > 0 ? Math.round((unifiedCount / (identity.profiles_created || 1)) * 100) : 0;
  const enrichmentPct  = unifiedCount > 0 ? Math.round((enrichedCount / unifiedCount) * 100) : 0;

  // Consent bar computation
  const totalCustomers  = identity.profiles_created || 1;
  const consentOptIn    = consent.opt_in || 0;
  const consentOptOut   = consent.opt_out || 0;
  const consentPending  = consent.pending || 0;
  const consentTotal    = consentOptIn + consentOptOut + consentPending || 1;
  const optInPct  = Math.round((consentOptIn / consentTotal) * 100);
  const optOutPct = Math.round((consentOptOut / consentTotal) * 100);
  const pendingPct = 100 - optInPct - optOutPct;

  return (
    <div className="flex-1 overflow-y-auto bg-[#f9fafb] h-full">
      {/* ─── Header ─── */}
      <header className="h-14 border-b border-gray-200 flex items-center justify-between px-8 bg-white shrink-0">
        <div>
          <h1 className="text-lg font-bold text-gray-900 leading-tight">CDP 360 Profile</h1>
          <p className="text-[11px] text-gray-500">Customer Data Platform — Unified Intelligence Pipeline</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-brand-600 hover:bg-brand-700 text-white rounded-lg shadow-sm transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing…' : 'Refresh Pipeline'}
        </button>
      </header>

      <div className="p-8 max-w-7xl space-y-6">

        {/* ═══════════ 1. PIPELINE FLOWCHART ═══════════ */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
          <h2 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">Pipeline Workflow — Live Status</h2>
          <div className="flex items-center justify-between">
            <PhaseCard name="Raw Data Collection"  icon={Database}  metric={`${totalEvents.toLocaleString()} events`}     progress={100}           theme="green" />
            <Arrow />
            <PhaseCard name="Identity Resolution"  icon={UserCheck} metric={`${processed.toLocaleString()} resolved`}    progress={identityPct}   theme="blue" />
            <Arrow />
            <PhaseCard name="Data Unification"     icon={GitMerge}  metric={`${unifiedCount.toLocaleString()} unified`}  progress={unificationPct} theme="purple" />
            <Arrow />
            <PhaseCard name="Profile Enrichment"   icon={Zap}       metric={`${enrichedCount.toLocaleString()} enriched`} progress={enrichmentPct}  theme="orange" />
            <Arrow />
            <PhaseCard name="Intelligence Layer"   icon={Brain}     metric={`${segmentsCount} segments`}                  progress={segmentsCount > 0 ? 100 : 0} theme="red" />
          </div>
        </div>

        {/* ═══════════ 2. RAW DATA COLLECTION PANEL ═══════════ */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
          <h2 className="text-base font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Database className="w-4 h-4 text-green-600" /> Raw Data Collection
            <span className="text-[10px] bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-semibold">LIVE</span>
          </h2>

          <div className="grid grid-cols-4 gap-4 mb-5">
            <KpiCard title="Events Today"  value={rawData.events_today || 0} />
            <KpiCard title="Total Events"  value={rawData.total_events || 0} />
            <KpiCard title="Pending"       value={rawData.events_pending || 0} accent={rawData.events_pending > 0 ? 'text-yellow-600' : 'text-gray-900'} />
            <KpiCard title="Errors"        value={rawData.events_errors || 0} accent={rawData.events_errors > 0 ? 'text-red-600' : 'text-gray-900'} />
          </div>

          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Recent Event Stream</h3>
          <div className="overflow-hidden border border-gray-200 rounded-lg">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase">Event Name</th>
                  <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase">Time</th>
                  <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {recentEvents.length > 0 ? recentEvents.map((ev: any, idx: number) => (
                  <tr key={ev.id || idx} className="hover:bg-gray-50">
                    <td className="px-4 py-2.5 text-sm">
                      <span className="font-medium text-brand-600">{ev.event_name}</span>
                    </td>
                    <td className="px-4 py-2.5 text-xs text-gray-500">
                      {ev.created_at ? new Date(ev.created_at).toLocaleString() : '—'}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded ${
                        ev.processed ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {ev.processed ? 'Processed' : 'Pending'}
                      </span>
                    </td>
                  </tr>
                )) : (
                  <tr><td colSpan={3} className="px-4 py-8 text-center text-gray-400 text-sm">No events ingested yet. Configure a data source to start collecting.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* ═══════════ 3. FEATURE CARDS ═══════════ */}
        <div className="grid grid-cols-5 gap-4">
          {/* Event Tracking */}
          <FeatureCard emoji="📡" title="Event Tracking" subtitle="Behavioral Signals">
            <div className="text-2xl font-bold text-gray-900 mb-2">{eventTracking.total_schemas || 0}</div>
            <div className="text-[10px] text-gray-500 mb-2">Registered Schemas</div>
            <div className="flex flex-wrap gap-1">
              {(eventTracking.event_types || []).slice(0, 6).map((t: string, i: number) => (
                <span key={i} className="px-1.5 py-0.5 bg-blue-50 text-blue-600 text-[9px] font-medium rounded">{t}</span>
              ))}
              {(eventTracking.event_types || []).length > 6 && (
                <span className="px-1.5 py-0.5 bg-gray-100 text-gray-500 text-[9px] font-medium rounded">
                  +{(eventTracking.event_types || []).length - 6} more
                </span>
              )}
            </div>
          </FeatureCard>

          {/* Segmentation */}
          <FeatureCard emoji="🎯" title="Segmentation" subtitle="Dynamic Audiences">
            <div className="text-2xl font-bold text-gray-900 mb-2">{segmentation.total_segments || 0}</div>
            <div className="text-[10px] text-gray-500 mb-2">Active Segments</div>
            <div className="space-y-1">
              {(segmentation.segments || []).slice(0, 4).map((s: any) => (
                <div key={s.id} className="flex justify-between text-[10px]">
                  <span className="text-gray-600 truncate mr-1">{s.name}</span>
                  <span className="text-gray-400 font-mono">{s.is_active ? '●' : '○'}</span>
                </div>
              ))}
            </div>
          </FeatureCard>

          {/* Enrichment */}
          <FeatureCard emoji="🔗" title="Enrichment" subtitle="Third-Party Data">
            <div className="text-2xl font-bold text-gray-900 mb-1">{enrichmentPct}%</div>
            <div className="text-[10px] text-gray-500 mb-2">Profiles Enriched</div>
            <div className="w-full bg-gray-100 rounded-full h-2 mb-1">
              <div className="bg-orange-500 h-2 rounded-full transition-all" style={{ width: `${enrichmentPct}%` }} />
            </div>
            <div className="text-[10px] text-gray-400">{enrichedCount} of {unifiedCount} profiles</div>
          </FeatureCard>

          {/* Distribution */}
          <FeatureCard emoji="⚡" title="Distribution" subtitle="Real-Time Activation">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse" />
              <span className="text-sm font-semibold text-gray-900">Active</span>
            </div>
            <div className="text-[10px] text-gray-500 space-y-1">
              <div>Webhooks: Real-time</div>
              <div>Email triggers: Enabled</div>
              <div>Cross-BIOM sync: Active</div>
            </div>
          </FeatureCard>

          {/* Consent Management */}
          <FeatureCard emoji="🛡️" title="Consent" subtitle="GDPR / CCPA">
            <div className="flex h-3 rounded-full overflow-hidden mb-2 border border-gray-200">
              <div className="bg-green-500 transition-all" style={{ width: `${optInPct}%` }} title={`Opt-in: ${optInPct}%`} />
              <div className="bg-gray-300 transition-all" style={{ width: `${pendingPct}%` }} title={`Pending: ${pendingPct}%`} />
              <div className="bg-red-400 transition-all" style={{ width: `${optOutPct}%` }} title={`Opt-out: ${optOutPct}%`} />
            </div>
            <div className="flex justify-between text-[9px] text-gray-500 mb-2">
              <span className="text-green-600 font-medium">In: {optInPct}%</span>
              <span>Pending: {pendingPct}%</span>
              <span className="text-red-500 font-medium">Out: {optOutPct}%</span>
            </div>
            <div className="text-[10px] text-gray-500 space-y-0.5">
              <div>DSAR Requests: <span className="font-semibold text-gray-700">{consent.dsar_requests || 0}</span></div>
              <div>RTBF Erasures: <span className="font-semibold text-gray-700">{consent.rtbf_erasures || 0}</span></div>
              <div>Audit Log: <span className="font-semibold text-gray-700">{(consent.audit_entries || 0).toLocaleString()}</span></div>
            </div>
          </FeatureCard>
        </div>

        {/* ═══════════ 4. IDENTITY RESOLUTION PANEL ═══════════ */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
          <h2 className="text-base font-bold text-gray-900 mb-4 flex items-center gap-2">
            <UserCheck className="w-4 h-4 text-blue-600" /> Identity Resolution
            <span className="text-[10px] bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-semibold">BACKEND PROCESSING</span>
          </h2>

          <div className="grid grid-cols-4 gap-4 mb-6">
            <KpiCard title="Deterministic Matches"   value={identity.deterministic_matches || 0} accent="text-green-700" />
            <KpiCard title="ML Batch Queue"           value={identity.ml_batch_queue || 0}       accent={identity.ml_batch_queue > 0 ? 'text-yellow-600' : 'text-gray-900'} />
            <KpiCard title="Auto-Merged (≥95%)"       value={identity.auto_merged || 0}          accent="text-blue-700" />
            <KpiCard title="Suggested Merges (70-94%)" value={identity.suggested_merges || 0}     accent={identity.suggested_merges > 0 ? 'text-orange-600' : 'text-gray-900'} />
          </div>

          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
            Merge Suggestion Queue
            {mergeSuggestions.length > 0 && (
              <span className="bg-orange-100 text-orange-700 text-[10px] px-2 py-0.5 rounded-full font-bold">
                {mergeSuggestions.length} pending
              </span>
            )}
          </h3>
          <div className="overflow-hidden border border-gray-200 rounded-lg">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase">Primary Customer</th>
                  <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase">Secondary Customer</th>
                  <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase">Confidence</th>
                  <th className="px-4 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase">Match Reasons</th>
                  <th className="px-4 py-2.5 text-center text-[10px] font-semibold text-gray-500 uppercase">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {mergeSuggestions.length > 0 ? mergeSuggestions.map((s: any) => {
                  const pct = Math.round((s.confidence_score || 0) * 100);
                  const isHigh = pct >= 95;
                  return (
                    <tr key={s.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <div className="font-medium text-gray-900 text-sm">{s.primary_email || s.primary_phone || '—'}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-gray-600 text-sm">{s.secondary_email || s.secondary_phone || '—'}</div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-sm font-bold ${isHigh ? 'text-green-600' : 'text-yellow-600'}`}>
                          {pct}%
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {(s.match_reasons || []).map((r: any, i: number) => (
                            <span key={i} className="px-1.5 py-0.5 bg-gray-100 text-gray-600 text-[9px] font-medium rounded border border-gray-200">
                              {typeof r === 'string' ? r : `${r.field}: ${Math.round((r.score || 0) * 100)}%`}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => handleApproveMerge(s.id)}
                            className="p-1.5 text-green-600 hover:bg-green-50 rounded-lg border border-transparent hover:border-green-200 transition-colors"
                            title="Approve Merge"
                          >
                            <Check className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleRejectMerge(s.id)}
                            className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg border border-transparent hover:border-red-200 transition-colors"
                            title="Reject"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                }) : (
                  <tr>
                    <td colSpan={5} className="px-4 py-10 text-center text-gray-400 text-sm">
                      No pending merge suggestions. The batch identity resolution engine will populate this queue on its next run.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
};
