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
        sources: []
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
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 mb-10">
      <h3 className="text-xl font-bold text-gray-900 mb-2">Horizon Copilot</h3>
      <p className="text-gray-500 text-sm mb-6">"What needs my attention?"</p>
      
      <div className="flex gap-2 mb-4">
        <input 
          type="text" 
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleAsk(query)}
          placeholder="Ask Horizon anything..." 
          className="flex-1 border border-gray-300 rounded px-4 py-2 text-sm focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
        />
        <button 
          onClick={() => handleAsk(query)}
          disabled={loading}
          className="bg-brand-600 text-white px-4 py-2 rounded text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
        >
          {loading ? "Asking..." : "Ask"}
        </button>
      </div>

      <div className="flex flex-wrap gap-2 mb-6">
        {suggestions.map(s => (
          <button 
            key={s} 
            onClick={() => handleAsk(s)}
            className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded-full transition-colors"
          >
            {s}
          </button>
        ))}
      </div>

      {response && (
        <div className="bg-gray-50 rounded-lg p-5 border border-gray-100 mt-4">
          <div className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed mb-4">
            {response.answer}
          </div>
          
          {response.sources && response.sources.length > 0 && (
            <div className="flex gap-3 flex-wrap">
              {response.sources.map((src: any, idx: number) => {
                if (src.type === 'deal') {
                  return (
                    <Link key={idx} to="/pipeline" className="text-xs font-medium bg-white border border-gray-200 text-brand-600 px-3 py-1.5 rounded shadow-sm hover:bg-gray-50">
                      View Deal
                    </Link>
                  );
                }
                if (src.type === 'customer') {
                  return (
                    <Link key={idx} to={`/customers/${src.id}/360`} className="text-xs font-medium bg-white border border-gray-200 text-brand-600 px-3 py-1.5 rounded shadow-sm hover:bg-gray-50">
                      Customer 360
                    </Link>
                  );
                }
                if (src.type === 'insight') {
                  return (
                    <span key={idx} className="text-xs font-medium bg-white border border-gray-200 text-gray-500 px-3 py-1.5 rounded shadow-sm">
                      View Insight
                    </span>
                  );
                }
                return null;
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
