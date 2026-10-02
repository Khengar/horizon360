import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { horizonApi } from '../api';
import {
  ArrowLeft, Play, Pause, Copy, Send, Sparkles, TrendingUp, Users,
  Target, DollarSign, CheckCircle2, AlertTriangle, ExternalLink, RefreshCw, BarChart2
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, LineChart, Line, AreaChart, Area
} from 'recharts';

export const CampaignAnalytics: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState<any>(null);
  const [campaign, setCampaign] = useState<any>(null);
  const [recipients, setRecipients] = useState<any[]>([]);
  const [recipientPage, setRecipientPage] = useState(1);
  const [briefing, setBriefing] = useState<any>(null);
  const [briefingLoading, setBriefingLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const loadData = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [campRes, anaRes, recipRes] = await Promise.all([
        horizonApi.getCampaign(id),
        horizonApi.getCampaignAnalytics(id),
        horizonApi.getCampaignRecipients(id, recipientPage).catch(() => ({ results: [] })),
      ]);
      setCampaign(campRes);
      setAnalytics(anaRes);
      setRecipients(Array.isArray(recipRes) ? recipRes : recipRes?.results || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [id, recipientPage]);

  // Load Attribution Narrative Briefing
  const fetchBriefing = async () => {
    if (!id) return;
    setBriefingLoading(true);
    try {
      const res = await horizonApi.getCampaignAttributionBriefing(id);
      setBriefing(res);
    } catch (err) {
      console.error(err);
    } finally {
      setBriefingLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      fetchBriefing();
    }
  }, [id]);

  const handlePause = async () => {
    if (!id) return;
    setActionLoading(true);
    await horizonApi.pauseCampaign(id);
    await loadData();
    setActionLoading(false);
  };

  const handleResume = async () => {
    if (!id) return;
    setActionLoading(true);
    await horizonApi.resumeCampaign(id);
    await loadData();
    setActionLoading(false);
  };

  const handleSendNow = async () => {
    if (!id) return;
    setActionLoading(true);
    await horizonApi.sendCampaignNow(id);
    await loadData();
    setActionLoading(false);
  };

  if (loading && !campaign) {
    return (
      <div className="flex-1 p-8 bg-gray-50 flex items-center justify-center h-full">
        <p className="text-gray-500 font-medium">Loading Campaign Intelligence...</p>
      </div>
    );
  }

  const kpis = analytics?.kpis || {};
  const financials = analytics?.financials || {};
  const banditVariants = analytics?.bandit_variants || [];
  const funnelData = analytics?.funnel || [];

  return (
    <div className="flex-1 p-8 bg-gray-50 h-full overflow-y-auto">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header & Controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/marketing')}
              className="p-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-100 text-gray-600 transition"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-gray-900">{campaign?.name}</h1>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                  campaign?.status === 'active' ? 'bg-green-100 text-green-800' :
                  campaign?.status === 'sending' ? 'bg-blue-100 text-blue-800 animate-pulse' :
                  campaign?.status === 'completed' ? 'bg-purple-100 text-purple-800' :
                  campaign?.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {campaign?.status}
                </span>
                <span className="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded capitalize">
                  {campaign?.channel}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Campaign ID: #{campaign?.id} • Goal: {campaign?.goal_event || 'conversion'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {campaign?.status === 'active' ? (
              <button
                onClick={handlePause}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-yellow-50 text-yellow-700 border border-yellow-300 rounded-lg text-xs font-semibold hover:bg-yellow-100"
              >
                <Pause className="w-3.5 h-3.5" /> Pause
              </button>
            ) : campaign?.status === 'paused' ? (
              <button
                onClick={handleResume}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-green-50 text-green-700 border border-green-300 rounded-lg text-xs font-semibold hover:bg-green-100"
              >
                <Play className="w-3.5 h-3.5" /> Resume
              </button>
            ) : campaign?.status === 'draft' || campaign?.status === 'scheduled' ? (
              <button
                onClick={handleSendNow}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-600 text-white rounded-lg text-xs font-semibold hover:bg-brand-700"
              >
                <Send className="w-3.5 h-3.5" /> Send Now
              </button>
            ) : null}

            <button
              onClick={() => navigate(`/marketing/campaigns/${campaign?.id}`)}
              className="px-3 py-1.5 bg-white border border-gray-300 rounded-lg text-xs font-medium text-gray-700 hover:bg-gray-50"
            >
              Edit Campaign
            </button>
          </div>
        </div>

        {/* KPI CARDS */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <span className="text-xs text-gray-500 font-semibold block mb-1">Total Recipients</span>
            <p className="text-2xl font-bold text-gray-900">{kpis.sent || 0}</p>
            <span className="text-xs text-gray-400 mt-1 block">Delivered: {kpis.delivered || 0} ({kpis.delivery_rate || 0}%)</span>
          </div>

          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <span className="text-xs text-gray-500 font-semibold block mb-1">Open Rate</span>
            <p className="text-2xl font-bold text-blue-600">{kpis.open_rate || 0}%</p>
            <span className="text-xs text-gray-400 mt-1 block">Total Opens: {kpis.opened || 0}</span>
          </div>

          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <span className="text-xs text-gray-500 font-semibold block mb-1">Click-Through Rate</span>
            <p className="text-2xl font-bold text-indigo-600">{kpis.click_rate || 0}%</p>
            <span className="text-xs text-gray-400 mt-1 block">Total Clicks: {kpis.clicked || 0}</span>
          </div>

          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <span className="text-xs text-gray-500 font-semibold block mb-1">Conversion Rate</span>
            <p className="text-2xl font-bold text-green-600">{kpis.conversion_rate || 0}%</p>
            <span className="text-xs text-gray-400 mt-1 block">Attributed Deals: {kpis.converted || 0}</span>
          </div>
        </div>

        {/* AI ATTRIBUTION NARRATIVE BRIEFING */}
        <div className="bg-gradient-to-r from-purple-900 to-indigo-900 rounded-xl p-6 text-white shadow-md">
          <div className="flex items-center justify-between mb-3 border-b border-purple-800/60 pb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-300" />
              <h3 className="text-base font-bold text-white">Marketing Agent Attribution Insight Briefing</h3>
            </div>
            <button
              onClick={fetchBriefing}
              disabled={briefingLoading}
              className="flex items-center gap-1.5 px-3 py-1 bg-white/10 hover:bg-white/20 rounded-lg text-xs font-medium text-purple-200 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${briefingLoading ? 'animate-spin' : ''}`} />
              Refresh Briefing
            </button>
          </div>

          <div className="text-sm text-purple-100 whitespace-pre-line leading-relaxed">
            {briefing?.narrative_briefing || 'Analyzing multi-touch attribution and calculating channel performance...'}
          </div>
        </div>

        {/* CONTEXTUAL MULTI-ARMED BANDIT LIVE WEIGHTS */}
        {campaign?.bandit_enabled && banditVariants.length > 0 && (
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-brand-600" /> Contextual Multi-Armed Bandit (Thompson Sampling)
                </h3>
                <p className="text-xs text-gray-500">Impression weights shift dynamically to higher performing creative variants.</p>
              </div>
              <span className="text-xs font-semibold px-2 py-1 bg-brand-50 text-brand-700 rounded border border-brand-200">
                Metric: {campaign.bandit_metric || 'click_rate'}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {banditVariants.map((v: any) => (
                <div key={v.id} className="p-4 bg-gray-50 rounded-lg border border-gray-200 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-gray-900">Variant {v.variant_name}</span>
                    <span className="text-xs font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                      {v.traffic_weight}% Traffic Weight
                    </span>
                  </div>

                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-brand-600 h-2 rounded-full transition-all"
                      style={{ width: `${v.traffic_weight}%` }}
                    />
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <div className="bg-white p-2 rounded border">
                      <span className="text-gray-400 block">Impressions</span>
                      <span className="font-bold text-gray-800">{v.impressions}</span>
                    </div>
                    <div className="bg-white p-2 rounded border">
                      <span className="text-gray-400 block">Successes</span>
                      <span className="font-bold text-green-600">{v.successes}</span>
                    </div>
                    <div className="bg-white p-2 rounded border">
                      <span className="text-gray-400 block">Conv Rate</span>
                      <span className="font-bold text-blue-600">{v.conversion_rate}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* FUNNEL & FINANCIALS */}
        <div className="grid grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <h3 className="text-base font-bold text-gray-900 mb-4">Campaign Conversion Funnel</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={funnelData} layout="vertical" margin={{ left: 20, right: 30 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e7eb" />
                  <XAxis type="number" tick={{ fontSize: 12, fill: '#6b7280' }} />
                  <YAxis dataKey="stage" type="category" tick={{ fontSize: 12, fill: '#374151' }} width={110} />
                  <Tooltip cursor={{ fill: '#f3f4f6' }} />
                  <Bar dataKey="count" fill="#4f46e5" radius={[0, 4, 4, 0]} barSize={24} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between">
            <div>
              <h3 className="text-base font-bold text-gray-900 mb-4">Financials & Multi-Touch ROI</h3>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="p-4 bg-red-50 rounded-lg border border-red-100">
                  <span className="text-xs text-red-600 font-semibold block">Total Campaign Spend</span>
                  <p className="text-2xl font-bold text-red-700">${financials.spend?.toFixed(2) || '0.00'}</p>
                </div>
                <div className="p-4 bg-green-50 rounded-lg border border-green-100">
                  <span className="text-xs text-green-600 font-semibold block">Attributed Revenue</span>
                  <p className="text-2xl font-bold text-green-700">${financials.roi?.toFixed(2) || '0.00'}</p>
                </div>
              </div>
            </div>

            <div className="p-4 bg-brand-50 rounded-lg border border-brand-200 text-center">
              <span className="text-xs text-brand-700 font-bold uppercase tracking-wider block">Net Attributed ROI</span>
              <p className="text-3xl font-extrabold text-brand-900 mt-1">{financials.roi_percentage || 0}%</p>
              <span className="text-xs text-brand-600 mt-1 block">
                Net Profit: ${(financials.net_profit || 0).toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* RECIPIENT DELIVERY LEDGER */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
            <h3 className="text-sm font-bold text-gray-900">Delivery & Interaction Ledger</h3>
            <span className="text-xs text-gray-500">Showing page {recipientPage}</span>
          </div>

          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Customer</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Variant</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Propensity</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">Last Touch</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {recipients.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500 text-sm">
                    No recipients queued yet. Launch the campaign to populate the ledger.
                  </td>
                </tr>
              ) : (
                recipients.map((r: any) => (
                  <tr key={r.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {r.customer_email || r.channel_address || 'Customer'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-600">
                      Variant {r.variant_name || 'A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-0.5 text-xs font-bold rounded-full capitalize ${
                        r.status === 'converted' ? 'bg-green-100 text-green-800' :
                        r.status === 'clicked' ? 'bg-indigo-100 text-indigo-800' :
                        r.status === 'opened' ? 'bg-blue-100 text-blue-800' :
                        r.status === 'delivered' ? 'bg-emerald-100 text-emerald-800' :
                        r.status === 'sent' ? 'bg-gray-100 text-gray-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {r.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-700">
                      {r.propensity_score ? `${(r.propensity_score * 100).toFixed(0)}%` : '—'}
                      {r.churn_risk && <span className="ml-1 text-red-500 font-bold">⚠️ Churn Risk</span>}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500 text-right">
                      {r.clicked_at ? new Date(r.clicked_at).toLocaleString() :
                       r.opened_at ? new Date(r.opened_at).toLocaleString() :
                       r.delivered_at ? new Date(r.delivered_at).toLocaleString() :
                       r.sent_at ? new Date(r.sent_at).toLocaleString() : 'Queued'}
                    </td>
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
