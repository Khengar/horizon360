import React, { useState } from 'react';

export const SettingsPage = () => {
  const token = localStorage.getItem('company_api_token') || 'Token not found. Please log out and log back in.';
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(token);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#f9fafb] p-8 overflow-y-auto">
      <div className="max-w-4xl mx-auto w-full">
        <h2 className="text-3xl font-bold text-gray-900 mb-6">Developer Settings</h2>
        
        {/* API Token Box */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Company API Token</h3>
          <p className="text-gray-500 text-sm mb-6">
            This token uniquely identifies your company. Use it to securely authenticate your backend servers when streaming events into the CDP via HTTP requests.
          </p>
          
          <div className="flex items-center gap-4">
            <div className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 font-mono text-sm text-gray-800 break-all">
              {token}
            </div>
            <button 
              onClick={handleCopy} 
              className="px-6 py-3 bg-brand-600 text-white font-medium rounded-lg hover:bg-brand-700 transition-colors cursor-pointer whitespace-nowrap"
            >
              {copied ? 'Copied!' : 'Copy Token'}
            </button>
          </div>
        </div>

        {/* Integration Guide */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Integration Guide</h3>
          <p className="text-gray-600 mb-6 text-sm">
            To stream events into Horizon 360, send a POST request to our ingestion endpoint. Ensure you include your API Token in the <code className="bg-gray-100 px-1 py-0.5 rounded text-gray-800">X-API-Key</code> header.
          </p>
          
          <div className="bg-[#1e293b] rounded-lg p-6 overflow-x-auto text-sm shadow-inner">
            <pre className="text-gray-300 font-mono leading-relaxed">
<span className="text-green-400">curl</span> -X POST http://localhost:8000/api/events/ \
  -H <span className="text-yellow-300">"Content-Type: application/json"</span> \
  -H <span className="text-yellow-300">"X-API-Key: &lt;YOUR_API_TOKEN&gt;"</span> \
  -d <span className="text-yellow-300">'{'{'}
  "event_name": "user.signup",
  "raw_payload": {'{'}
    "email": "customer@example.com",
    "plan": "enterprise"
  {'}'}
{'}'}'</span>
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};
