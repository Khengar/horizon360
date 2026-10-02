import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { horizonApi } from '../api';
import {
  ArrowLeft, ArrowRight, CheckCircle2, Sparkles, Send, Calendar,
  Users, Mail, MessageSquare, Globe, Target, AlertCircle, Plus, Trash2, Eye, ShieldCheck
} from 'lucide-react';

export const CampaignBuilder: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id?: string }>();
  const isEditing = Boolean(id);

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  // Available CDP Segments
  const [availableSegments, setAvailableSegments] = useState<any[]>([]);

  // Form State
  const [campaign, setCampaign] = useState<any>({
    name: '',
    description: '',
    channel: 'email',
    campaign_type: 'one_time',
    budget: '500.00',
    goal_event: 'deal.won',
    goal_value: '2500.00',
    bandit_enabled: true,
    bandit_metric: 'click_rate',
    sender_name: 'Horizon360 Marketing',
    sender_email: 'hello@horizon360.ai',
    reply_to: 'support@horizon360.ai',
    ai_audience_enabled: true,
    ai_copy_enabled: true,
    ai_send_time_enabled: true,
    scheduled_at: '',
    timezone: 'UTC',
    segment_ids: [] as string[],
  });

  // Content Variants State
  const [variants, setVariants] = useState<any[]>([
    {
      id: 'temp-1',
      variant_name: 'A',
      subject: 'Transform Your Operations with Horizon360',
      preview_text: 'See how unified workflows reduce operational friction.',
      body_html: '<p>Hi {{ customer.name }},</p><p>We noticed your team is scaling. Discover how Horizon360 unifies your data and automates cross-BIOM intelligence.</p>',
      body_plain: 'Hi {{ customer.name }},\n\nWe noticed your team is scaling. Discover how Horizon360 unifies your data and automates cross-BIOM intelligence.',
      message_text: 'Hi {{ customer.name }}, scale faster with Horizon360: https://horizon360.ai',
      cta_text: 'Schedule Platform Demo',
      cta_url: 'https://horizon360.ai/demo',
      traffic_percentage: 50,
    },
    {
      id: 'temp-2',
      variant_name: 'B',
      subject: 'Are Disconnected Lists Slowing Your Team Down?',
      preview_text: 'Eliminate data duplication with the Universal Data Model.',
      body_html: '<p>Hi {{ customer.name }},</p><p>Stop managing isolated spreadsheets. Operate directly on shared customer nodes across sales, marketing, and service.</p>',
      body_plain: 'Hi {{ customer.name }},\n\nStop managing isolated spreadsheets. Operate directly on shared customer nodes across sales, marketing, and service.',
      message_text: 'Hi {{ customer.name }}, eliminate disconnected lists: https://horizon360.ai',
      cta_text: 'See UDM in Action',
      cta_url: 'https://horizon360.ai/udm',
      traffic_percentage: 50,
    }
  ]);

  // Audience Preview State
  const [previewData, setPreviewData] = useState<any>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  // AI Generation State
  const [aiAudienceLoading, setAiAudienceLoading] = useState(false);
  const [aiAudienceResult, setAiAudienceResult] = useState<any>(null);
  const [aiCopyLoading, setAiCopyLoading] = useState(false);
  const [previewModalContent, setPreviewModalContent] = useState<any>(null);

  // Load existing campaign data if editing
  useEffect(() => {
    // Load segments
    horizonApi.getAllSegments().catch(() => []).then(segs => {
      setAvailableSegments(Array.isArray(segs) ? segs : segs?.results || []);
    });

    if (id) {
      setLoading(true);
      horizonApi.getCampaign(id).then(data => {
        setCampaign({
          ...data,
          segment_ids: data.campaign_segments?.map((cs: any) => cs.segment) || []
        });
        if (data.contents && data.contents.length > 0) {
          setVariants(data.contents);
        }
        setLoading(false);
      }).catch(err => {
        console.error(err);
        setLoading(false);
      });
    }
  }, [id]);

  // Handle Audience Preview
  const handlePreviewAudience = async () => {
    setPreviewLoading(true);
    try {
      let campaignId: string | number | undefined = id || campaign.id;
      if (!campaignId) {
        // Create draft first
        const saved = await horizonApi.createCampaign({ ...campaign, status: 'draft' });
        campaignId = saved.id;
        setCampaign((prev: any) => ({ ...prev, id: saved.id }));
      } else {
        await horizonApi.updateCampaign(campaignId, campaign);
      }
      if (!campaignId) return;
      const res = await horizonApi.previewCampaignAudience(campaignId);
      setPreviewData(res);
    } catch (err) {
      console.error(err);
      alert('Failed to preview audience. Please check campaign settings.');
    } finally {
      setPreviewLoading(false);
    }
  };

  // Autonomous Audience Generation
  const handleGenerateAiAudience = async () => {
    setAiAudienceLoading(true);
    try {
      let campaignId: string | number | undefined = campaign.id || id;
      if (!campaignId) {
        const saved = await horizonApi.createCampaign({ ...campaign, status: 'draft' });
        campaignId = saved.id;
        setCampaign((prev: any) => ({ ...prev, id: saved.id }));
      }
      if (!campaignId) return;
      const res = await horizonApi.generateCampaignAudience(campaignId, { save_as_segment: true });
      setAiAudienceResult(res);
      if (res.created_segment_id) {
        setCampaign((prev: any) => ({
          ...prev,
          segment_ids: [...prev.segment_ids, res.created_segment_id]
        }));
        // Reload segments
        const segs = await horizonApi.getAllSegments().catch(() => []);
        setAvailableSegments(Array.isArray(segs) ? segs : segs?.results || []);
      }
    } catch (err) {
      console.error(err);
      alert('Failed to generate AI audience cohort.');
    } finally {
      setAiAudienceLoading(false);
    }
  };

  // AI Copy Generation
  const handleGenerateAiCopy = async () => {
    setAiCopyLoading(true);
    try {
      let campaignId: string | number | undefined = campaign.id || id;
      if (!campaignId) {
        const saved = await horizonApi.createCampaign({ ...campaign, status: 'draft' });
        campaignId = saved.id;
        setCampaign((prev: any) => ({ ...prev, id: saved.id }));
      }
      if (!campaignId) return;
      const nextVariantLetter = String.fromCharCode(65 + variants.length);
      const res = await horizonApi.generateCampaignCopy(campaignId, {
        variant_name: nextVariantLetter,
        tone: 'compelling, data-driven and high-conversion'
      });
      setVariants(prev => [...prev, res]);
    } catch (err) {
      console.error(err);
      alert('Failed to generate AI copy variant.');
    } finally {
      setAiCopyLoading(false);
    }
  };

  // Launch Campaign
  const handleLaunchCampaign = async (sendImmediately: boolean) => {
    setSaving(true);
    try {
      let campaignId: string | number | undefined = campaign.id || id;
      const payload = {
        ...campaign,
        status: sendImmediately ? 'sending' : (campaign.scheduled_at ? 'scheduled' : 'draft')
      };

      if (!campaignId) {
        const created = await horizonApi.createCampaign(payload);
        campaignId = created.id;
      } else {
        await horizonApi.updateCampaign(campaignId, payload);
      }

      if (!campaignId) return;

      // Save variants if newly added
      for (const variant of variants) {
        if (typeof variant.id === 'string' && variant.id.startsWith('temp-')) {
          await horizonApi.createCampaignContent({
            ...variant,
            campaign: campaignId
          });
        } else if (variant.id) {
          await horizonApi.updateCampaignContent(variant.id, variant);
        }
      }

      if (sendImmediately) {
        await horizonApi.sendCampaignNow(campaignId);
      } else if (campaign.scheduled_at) {
        await horizonApi.scheduleCampaign(campaignId, {
          scheduled_at: campaign.scheduled_at,
          timezone: campaign.timezone
        });
      }

      navigate(`/marketing`);
    } catch (err) {
      console.error(err);
      alert('Failed to launch campaign. Check console.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex-1 p-8 bg-gray-50 h-full overflow-y-auto">
      <div className="max-w-5xl mx-auto">
        
        {/* Navigation & Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/marketing')}
              className="p-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-100 text-gray-600 transition"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {isEditing ? 'Edit Campaign' : 'Create Multi-Channel Campaign'}
              </h1>
              <p className="text-sm text-gray-500">
                Universal Data Model • Contextual Bandit • Send-Time AI
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => handleLaunchCampaign(false)}
              disabled={saving}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition"
            >
              Save Draft
            </button>
          </div>
        </div>

        {/* Step Indicator */}
        <div className="grid grid-cols-5 gap-2 mb-8 bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
          {[
            { num: 1, label: 'Setup', icon: Target },
            { num: 2, label: 'Audience', icon: Users },
            { num: 3, label: 'Creative', icon: Sparkles },
            { num: 4, label: 'Schedule', icon: Calendar },
            { num: 5, label: 'Review', icon: CheckCircle2 },
          ].map(s => (
            <button
              key={s.num}
              onClick={() => setStep(s.num)}
              className={`flex items-center gap-3 p-2 rounded-lg text-left transition ${
                step === s.num
                  ? 'bg-brand-50 border border-brand-200 text-brand-700'
                  : step > s.num
                  ? 'text-green-600'
                  : 'text-gray-400'
              }`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${
                step === s.num
                  ? 'bg-brand-600 text-white'
                  : step > s.num
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-500'
              }`}>
                {s.num}
              </div>
              <div className="hidden sm:block">
                <p className="text-xs font-semibold leading-tight">{s.label}</p>
                <span className="text-[10px] text-gray-400">Step {s.num}</span>
              </div>
            </button>
          ))}
        </div>

        {/* STEP 1: CAMPAIGN SETUP */}
        {step === 1 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-6">
            <h2 className="text-lg font-bold text-gray-900 border-b pb-3">Step 1: Campaign Configuration</h2>

            <div className="grid grid-cols-2 gap-6">
              <div className="col-span-2">
                <label className="block text-sm font-semibold text-gray-700 mb-1">Campaign Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Q4 Global Enterprise Expansion"
                  value={campaign.name}
                  onChange={e => setCampaign({ ...campaign, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Delivery Channel</label>
                <select
                  value={campaign.channel}
                  onChange={e => setCampaign({ ...campaign, channel: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500"
                >
                  <option value="email">Email Campaign</option>
                  <option value="sms">SMS Text Message</option>
                  <option value="digital_ads">Digital Ad Audience Sync</option>
                  <option value="web_engagement">Web Onsite Personalization</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Campaign Type</label>
                <select
                  value={campaign.campaign_type}
                  onChange={e => setCampaign({ ...campaign, campaign_type: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500"
                >
                  <option value="one_time">One-Time Blast</option>
                  <option value="automated">Automated Journey</option>
                  <option value="triggered">Event-Triggered</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Allocated Budget ($)</label>
                <input
                  type="number"
                  step="0.01"
                  value={campaign.budget}
                  onChange={e => setCampaign({ ...campaign, budget: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Goal Event (Attribution Target)</label>
                <input
                  type="text"
                  placeholder="e.g. deal.won, lead.qualified"
                  value={campaign.goal_event}
                  onChange={e => setCampaign({ ...campaign, goal_event: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-semibold text-gray-700 mb-1">Description & Strategic Intent</label>
                <textarea
                  rows={3}
                  placeholder="Describe target personas, intended outcome, and key value propositions..."
                  value={campaign.description}
                  onChange={e => setCampaign({ ...campaign, description: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
            </div>

            {/* AI Innovation Toggles */}
            <div className="border-t pt-4">
              <h3 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-600" /> AI Innovations & System Capabilities
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <label className="flex items-start gap-3 p-3 bg-purple-50/50 rounded-lg border border-purple-100 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={campaign.bandit_enabled}
                    onChange={e => setCampaign({ ...campaign, bandit_enabled: e.target.checked })}
                    className="mt-1 text-purple-600 rounded"
                  />
                  <div>
                    <span className="text-sm font-semibold text-gray-900">Contextual Multi-Armed Bandit</span>
                    <p className="text-xs text-gray-500">Thompson Sampling replaces static splits, automatically shifting impression weight to winning creatives in real-time.</p>
                  </div>
                </label>

                <label className="flex items-start gap-3 p-3 bg-blue-50/50 rounded-lg border border-blue-100 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={campaign.ai_send_time_enabled}
                    onChange={e => setCampaign({ ...campaign, ai_send_time_enabled: e.target.checked })}
                    className="mt-1 text-blue-600 rounded"
                  />
                  <div>
                    <span className="text-sm font-semibold text-gray-900">Predictive Propensity & Send-Time</span>
                    <p className="text-xs text-gray-500">Forecast conversion probability, detect churn risks, and pinpoint individual delivery windows per recipient.</p>
                  </div>
                </label>
              </div>
            </div>

            <div className="flex justify-end pt-4 border-t">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="flex items-center gap-2 bg-brand-600 text-white px-6 py-2.5 rounded-lg text-sm font-semibold hover:bg-brand-700 transition"
              >
                Proceed to Audience <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: AUDIENCE TARGETING */}
        {step === 2 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-6">
            <div className="flex items-center justify-between border-b pb-3">
              <div>
                <h2 className="text-lg font-bold text-gray-900">Step 2: Universal Data Model Audience</h2>
                <p className="text-xs text-gray-500">Directly targets shared Customer nodes with strict GDPR/CCPA consent enforcement.</p>
              </div>
              <button
                type="button"
                onClick={handleGenerateAiAudience}
                disabled={aiAudienceLoading}
                className="flex items-center gap-2 px-3 py-1.5 bg-purple-50 text-purple-700 border border-purple-200 rounded-lg text-xs font-semibold hover:bg-purple-100 transition"
              >
                <Sparkles className="w-3.5 h-3.5" />
                {aiAudienceLoading ? 'Reasoning over UDM...' : 'Generate Lookalike Cohort (LangGraph AI)'}
              </button>
            </div>

            {aiAudienceResult && (
              <div className="p-4 bg-purple-50 rounded-lg border border-purple-200 text-sm">
                <p className="font-semibold text-purple-900 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-600" /> AI Recommendation Generated:
                </p>
                <p className="text-xs text-purple-800 mt-1">{aiAudienceResult.rationale}</p>
                <div className="mt-2 flex gap-2 flex-wrap">
                  {aiAudienceResult.recommended_rules?.map((r: any, idx: number) => (
                    <span key={idx} className="px-2 py-0.5 bg-white border border-purple-200 rounded text-[11px] font-mono text-purple-700">
                      {r.field} {r.operator} {r.value}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Select Target Segments</label>
              <div className="grid grid-cols-2 gap-3 max-h-60 overflow-y-auto p-1">
                {availableSegments.map(seg => {
                  const isSelected = campaign.segment_ids?.includes(seg.id);
                  return (
                    <div
                      key={seg.id}
                      onClick={() => {
                        const next = isSelected
                          ? campaign.segment_ids.filter((sid: string) => sid !== seg.id)
                          : [...campaign.segment_ids, seg.id];
                        setCampaign({ ...campaign, segment_ids: next });
                      }}
                      className={`p-3 rounded-lg border cursor-pointer transition flex items-start gap-3 ${
                        isSelected ? 'border-brand-500 bg-brand-50/50' : 'border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {}}
                        className="mt-1 text-brand-600 rounded"
                      />
                      <div>
                        <p className="text-sm font-semibold text-gray-900">{seg.name}</p>
                        <p className="text-xs text-gray-500 truncate">{seg.description || 'Dynamic rule-based audience'}</p>
                        <span className="text-[10px] text-gray-400 mt-1 inline-block">
                          {seg.rules?.length || 0} predicates applied
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Audience Preview Diagnostics */}
            <div className="bg-gray-50 p-4 rounded-xl border border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-bold text-gray-900 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-green-600" /> Real-Time Consent & Audience Gate
                </span>
                <button
                  type="button"
                  onClick={handlePreviewAudience}
                  disabled={previewLoading}
                  className="px-3 py-1.5 bg-white border border-gray-300 rounded-lg text-xs font-semibold hover:bg-gray-100 transition"
                >
                  {previewLoading ? 'Evaluating Predicates...' : 'Evaluate & Preview Audience'}
                </button>
              </div>

              {previewData ? (
                <div className="grid grid-cols-3 gap-4 text-center mt-3">
                  <div className="p-3 bg-white rounded-lg border">
                    <p className="text-xs text-gray-500 font-medium">Estimated Audience</p>
                    <p className="text-xl font-bold text-brand-600">{previewData.estimated_audience}</p>
                  </div>
                  <div className="p-3 bg-white rounded-lg border">
                    <p className="text-xs text-gray-500 font-medium">Consent Verified</p>
                    <p className="text-xl font-bold text-green-600">{previewData.consented_recipients}</p>
                  </div>
                  <div className="p-3 bg-white rounded-lg border">
                    <p className="text-xs text-gray-500 font-medium">Target Channel</p>
                    <p className="text-xl font-bold text-gray-700 capitalize">{previewData.channel}</p>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-gray-500 text-center py-2">
                  Click "Evaluate & Preview Audience" to calculate eligible recipients and verify privacy consent.
                </p>
              )}
            </div>

            <div className="flex justify-between pt-4 border-t">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-100"
              >
                Back
              </button>
              <button
                type="button"
                onClick={() => setStep(3)}
                className="flex items-center gap-2 bg-brand-600 text-white px-6 py-2.5 rounded-lg text-sm font-semibold hover:bg-brand-700 transition"
              >
                Proceed to Creative <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: CREATIVE & VARIANTS */}
        {step === 3 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-6">
            <div className="flex items-center justify-between border-b pb-3">
              <div>
                <h2 className="text-lg font-bold text-gray-900">Step 3: Creative Variants & Multi-Armed Bandit</h2>
                <p className="text-xs text-gray-500">Define multiple creative variants. The bandit shifts impression weight to top performers automatically.</p>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={handleGenerateAiCopy}
                  disabled={aiCopyLoading}
                  className="flex items-center gap-2 px-3 py-1.5 bg-purple-50 text-purple-700 border border-purple-200 rounded-lg text-xs font-semibold hover:bg-purple-100 transition"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  {aiCopyLoading ? 'Synthesizing...' : 'Generate Variant (RAG Copy AI)'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const nextLetter = String.fromCharCode(65 + variants.length);
                    setVariants([
                      ...variants,
                      {
                        id: `temp-${Date.now()}`,
                        variant_name: nextLetter,
                        subject: `New Angle - Variant ${nextLetter}`,
                        body_html: '<p>Hi {{ customer.name }},</p><p>Check out our latest update.</p>',
                        body_plain: 'Hi {{ customer.name }},\n\nCheck out our latest update.',
                        traffic_percentage: 50,
                      }
                    ]);
                  }}
                  className="flex items-center gap-1 px-3 py-1.5 border border-gray-300 rounded-lg text-xs font-semibold hover:bg-gray-50"
                >
                  <Plus className="w-3.5 h-3.5" /> Add Variant
                </button>
              </div>
            </div>

            <div className="space-y-6">
              {variants.map((v, idx) => (
                <div key={v.id || idx} className="p-5 bg-gray-50 rounded-xl border border-gray-200 space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="px-3 py-1 bg-brand-100 text-brand-800 text-xs font-bold rounded-full">
                      Variant {v.variant_name}
                    </span>
                    {variants.length > 1 && (
                      <button
                        type="button"
                        onClick={() => setVariants(variants.filter((_, i) => i !== idx))}
                        className="text-red-500 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>

                  {campaign.channel === 'email' ? (
                    <>
                      <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1">Subject Line</label>
                        <input
                          type="text"
                          value={v.subject || ''}
                          onChange={e => {
                            const updated = [...variants];
                            updated[idx].subject = e.target.value;
                            setVariants(updated);
                          }}
                          className="w-full px-3 py-2 border rounded-lg text-sm bg-white"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1">Preview Snippet</label>
                        <input
                          type="text"
                          value={v.preview_text || ''}
                          onChange={e => {
                            const updated = [...variants];
                            updated[idx].preview_text = e.target.value;
                            setVariants(updated);
                          }}
                          className="w-full px-3 py-2 border rounded-lg text-sm bg-white"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1">Body HTML (Supports {'{{ customer.name }}'})</label>
                        <textarea
                          rows={4}
                          value={v.body_html || ''}
                          onChange={e => {
                            const updated = [...variants];
                            updated[idx].body_html = e.target.value;
                            setVariants(updated);
                          }}
                          className="w-full px-3 py-2 border rounded-lg text-sm font-mono bg-white"
                        />
                      </div>
                    </>
                  ) : (
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1">Message Text</label>
                      <textarea
                        rows={3}
                        value={v.message_text || ''}
                        onChange={e => {
                          const updated = [...variants];
                          updated[idx].message_text = e.target.value;
                          setVariants(updated);
                        }}
                        className="w-full px-3 py-2 border rounded-lg text-sm bg-white"
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="flex justify-between pt-4 border-t">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-100"
              >
                Back
              </button>
              <button
                type="button"
                onClick={() => setStep(4)}
                className="flex items-center gap-2 bg-brand-600 text-white px-6 py-2.5 rounded-lg text-sm font-semibold hover:bg-brand-700 transition"
              >
                Proceed to Schedule <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 4: SCHEDULE & SENDER IDENTITY */}
        {step === 4 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-6">
            <h2 className="text-lg font-bold text-gray-900 border-b pb-3">Step 4: Dispatch & Sender Identity</h2>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Sender Display Name</label>
                <input
                  type="text"
                  value={campaign.sender_name}
                  onChange={e => setCampaign({ ...campaign, sender_name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Sender Email</label>
                <input
                  type="email"
                  value={campaign.sender_email}
                  onChange={e => setCampaign({ ...campaign, sender_email: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                />
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-semibold text-gray-700 mb-1">Schedule Send Time (Optional)</label>
                <input
                  type="datetime-local"
                  value={campaign.scheduled_at}
                  onChange={e => setCampaign({ ...campaign, scheduled_at: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                />
                <span className="text-xs text-gray-400 mt-1 block">Leave empty to launch immediately upon approval.</span>
              </div>
            </div>

            <div className="flex justify-between pt-4 border-t">
              <button
                type="button"
                onClick={() => setStep(3)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-100"
              >
                Back
              </button>
              <button
                type="button"
                onClick={() => setStep(5)}
                className="flex items-center gap-2 bg-brand-600 text-white px-6 py-2.5 rounded-lg text-sm font-semibold hover:bg-brand-700 transition"
              >
                Review & Launch <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 5: REVIEW & LAUNCH */}
        {step === 5 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-6">
            <h2 className="text-lg font-bold text-gray-900 border-b pb-3">Step 5: Pre-Flight Review & Launch</h2>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="p-4 bg-gray-50 rounded-lg">
                <span className="text-xs text-gray-500 font-semibold block mb-1">Campaign</span>
                <p className="font-bold text-gray-900">{campaign.name || 'Untitled Campaign'}</p>
                <p className="text-xs text-gray-500 mt-1 capitalize">{campaign.channel} • {campaign.campaign_type}</p>
              </div>

              <div className="p-4 bg-gray-50 rounded-lg">
                <span className="text-xs text-gray-500 font-semibold block mb-1">Estimated Audience</span>
                <p className="font-bold text-brand-600">{previewData?.estimated_audience || campaign.estimated_audience || 'Ready'}</p>
                <p className="text-xs text-green-600 mt-1">Consent Verified (GDPR/CCPA)</p>
              </div>

              <div className="p-4 bg-gray-50 rounded-lg">
                <span className="text-xs text-gray-500 font-semibold block mb-1">Creative Variants</span>
                <p className="font-bold text-gray-900">{variants.length} Variants Configured</p>
                <p className="text-xs text-purple-600 mt-1">
                  {campaign.bandit_enabled ? 'Multi-Armed Bandit Active' : 'Static Distribution'}
                </p>
              </div>

              <div className="p-4 bg-gray-50 rounded-lg">
                <span className="text-xs text-gray-500 font-semibold block mb-1">Execution Mode</span>
                <p className="font-bold text-gray-900">
                  {campaign.scheduled_at ? `Scheduled for ${campaign.scheduled_at}` : 'Immediate Outbound Send'}
                </p>
                <p className="text-xs text-gray-500 mt-1">Async Celery Task Pipeline</p>
              </div>
            </div>

            <div className="flex justify-between pt-6 border-t">
              <button
                type="button"
                onClick={() => setStep(4)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-100"
              >
                Back
              </button>
              <div className="flex gap-3">
                <button
                  type="button"
                  disabled={saving}
                  onClick={() => handleLaunchCampaign(false)}
                  className="px-5 py-2.5 bg-gray-100 text-gray-700 rounded-lg text-sm font-semibold hover:bg-gray-200 transition"
                >
                  Save as Draft
                </button>
                <button
                  type="button"
                  disabled={saving}
                  onClick={() => handleLaunchCampaign(true)}
                  className="flex items-center gap-2 px-6 py-2.5 bg-brand-600 text-white rounded-lg text-sm font-bold hover:bg-brand-700 shadow-md transition"
                >
                  <Send className="w-4 h-4" />
                  {saving ? 'Dispatching...' : 'Launch Campaign Now'}
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
