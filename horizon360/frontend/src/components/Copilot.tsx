import React, { useState } from 'react';
import { horizonApi } from '../api';
import { Link } from 'react-router-dom';

export const Copilot = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);
  
  const handleAsk = async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    setResponse(null);
    setQuery(q);
    try {
      const res = await horizonApi.askCopilot(q);
      setResponse(res);
    } catch (err) {
      setResponse({
        status: "error",
        answer: "An error occurred while communicating with the Copilot.",
        sources: [],
        provider: "Offline Fallback"
      });
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    "What deals are at risk?",
    "What's our current pipeline?",
    "Tell me about alice@example.com",
    "Why is Enterprise License at risk?",
    "What should sales focus on?"
  ];

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6 mb-10">
      <div className="flex justify-between items-center mb-2">
        <div>
          <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            Horizon Copilot
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-brand-50 text-brand-700 border border-brand-200">
              Autonomous Agent
            </span>
          </h3>
          <p className="text-gray-500 text-sm">"What needs my attention across the universal data model?"</p>
        </div>
        {response?.provider && (
          <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2.5 py-1 rounded-md border border-gray-200">
            Powered by: <strong className="text-gray-700">{response.provider}</strong>
          </span>
        )}
      </div>
      
      <div className="flex gap-2 mb-4 mt-4">
        <input 
          type="text" 
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleAsk(query)}
          placeholder="Ask Horizon Copilot (e.g. 'What deals are stalled?' or 'Summarize pipeline')..." 
          className="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
        />
        <button 
          onClick={() => handleAsk(query)}
          disabled={loading}
          className="bg-brand-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50 transition-colors shadow-sm"
        >
          {loading ? "Analyzing..." : "Ask Agent"}
        </button>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        {suggestions.map(s => (
          <button 
            key={s} 
            onClick={() => handleAsk(s)}
            className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded-full transition-colors font-medium"
          >
            {s}
          </button>
        ))}
      </div>

      {response && (
        <div className="bg-gray-50 rounded-xl p-5 border border-gray-200 mt-4">
          <div className="flex justify-between items-center mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-700">
              Grounded Analysis
            </span>
            {response.intent && (
              <span className="text-xs bg-white text-gray-500 px-2 py-0.5 rounded border border-gray-200">
                Intent: {response.intent}
              </span>
            )}
          </div>

          <div className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed mb-4 bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
            {response.answer}
          </div>
          
          {/* Action and Source Badges */}
          <div className="flex flex-wrap gap-2 items-center">
            {response.actions && response.actions.map((act: any, idx: number) => {
              if (act.type === 'navigate') {
                return (
                  <Link 
                    key={`act-${idx}`} 
                    to={act.target} 
                    className="text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white px-3 py-1.5 rounded-md shadow-sm transition-colors"
                  >
                    → {act.label}
                  </Link>
                );
              }
              return (
                <button 
                  key={`act-${idx}`} 
                  onClick={() => alert(`Action triggered: ${act.action_name || act.label}`)}
                  className="text-xs font-semibold bg-brand-50 hover:bg-brand-100 text-brand-700 border border-brand-200 px-3 py-1.5 rounded-md transition-colors"
                >
                  ⚡ {act.label}
                </button>
              );
            })}

            {response.sources && response.sources.length > 0 && response.sources.map((src: any, idx: number) => {
              if (src.type === 'deal') {
                return (
                  <Link key={`src-${idx}`} to="/pipeline" className="text-xs font-medium bg-white border border-gray-200 text-brand-600 px-3 py-1.5 rounded-md shadow-sm hover:bg-gray-50">
                    Deal #{src.id}
                  </Link>
                );
              }
              if (src.type === 'customer') {
                return (
                  <Link key={`src-${idx}`} to={`/customers/${src.id}/360`} className="text-xs font-medium bg-white border border-gray-200 text-brand-600 px-3 py-1.5 rounded-md shadow-sm hover:bg-gray-50">
                    Customer 360
                  </Link>
                );
              }
              if (src.type === 'insight') {
                return (
                  <span key={`src-${idx}`} className="text-xs font-medium bg-white border border-gray-200 text-gray-600 px-3 py-1.5 rounded-md shadow-sm">
                    Insight #{src.id}
                  </span>
                );
              }
              return null;
            })}
          </div>
        </div>
      )}
    </div>
  );
};
