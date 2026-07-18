import React, { useState } from 'react';

export const CustomerTable = ({ customers }: { customers: any[] }) => {
  const [selectedCustomer, setSelectedCustomer] = useState<any>(null);

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
      <div className="px-5 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
        <h3 className="font-semibold text-gray-800">Unified Profiles Directory</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-gray-600">
          <thead className="bg-white text-xs text-gray-400 uppercase tracking-wider border-b border-gray-200">
            <tr>
              <th className="px-5 py-3 font-medium">Customer</th>
              <th className="px-5 py-3 font-medium">Primary Email</th>
              <th className="px-5 py-3 font-medium">Phone</th>
              <th className="px-5 py-3 font-medium">Status / Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {customers.map((c, idx) => (
              <tr key={c.id || idx} className="hover:bg-gray-50">
                <td className="px-5 py-4">
                  <div className="font-medium text-gray-900">ID: {c.id?.substring(0,8) || 'Unknown'}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{c.timeline?.length || 0} events tracked</div>
                </td>
                <td className="px-5 py-4">{c.primary_email || '--'}</td>
                <td className="px-5 py-4">{c.primary_phone || '--'}</td>
                <td className="px-5 py-4">
                   <button 
                     onClick={() => setSelectedCustomer(c)}
                     className="px-3 py-1 text-xs font-medium text-brand-600 bg-brand-50 border border-brand-200 rounded hover:bg-brand-100 transition-colors cursor-pointer"
                   >
                     View Profile
                   </button>
                </td>
              </tr>
            ))}
            {customers.length === 0 && (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                  No customers found. Make sure the Django API is running.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Profile Modal */}
      {selectedCustomer && (
        <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
              <h2 className="text-lg font-bold text-gray-900">
                Profile Timeline: {selectedCustomer.primary_email || selectedCustomer.id}
              </h2>
              <button onClick={() => setSelectedCustomer(null)} className="text-gray-500 hover:text-gray-800 cursor-pointer">
                ✕ Close
              </button>
            </div>
            <div className="p-6 overflow-y-auto bg-gray-50 flex-1">
              <div className="flex justify-end mb-4">
                <button 
                  onClick={() => {
                    navigator.clipboard.writeText(JSON.stringify(selectedCustomer.timeline, null, 2));
                    alert('Copied to clipboard!');
                  }}
                  className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 cursor-pointer shadow-sm flex items-center"
                >
                  <span className="mr-2">📋</span> Copy Raw JSON
                </button>
              </div>
              
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
                <table className="w-full text-left text-sm text-gray-600">
                  <thead className="bg-gray-50 text-xs text-gray-400 uppercase tracking-wider border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 font-medium">Timestamp</th>
                      <th className="px-4 py-3 font-medium">Event Action</th>
                      <th className="px-4 py-3 font-medium">Event Properties</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {selectedCustomer.timeline?.map((ev: any, i: number) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap text-gray-500 text-xs">
                          {ev.timestamp ? new Date(ev.timestamp).toLocaleString() : 'N/A'}
                        </td>
                        <td className="px-4 py-3 font-semibold text-brand-600 align-top whitespace-nowrap">
                          {ev.event_name || 'unknown.event'}
                        </td>
                        <td className="px-4 py-3 align-top">
                          <div className="flex flex-wrap gap-1.5">
                            {Object.entries(ev).map(([key, val]) => {
                              if (key === 'event_name' || key === 'timestamp') return null;
                              return (
                                <span key={key} className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-50 text-gray-700 border border-gray-200">
                                  <span className="font-semibold text-gray-500 mr-1">{key}:</span> 
                                  {typeof val === 'object' ? '{...}' : String(val)}
                                </span>
                              );
                            })}
                          </div>
                        </td>
                      </tr>
                    ))}
                    {(!selectedCustomer.timeline || selectedCustomer.timeline.length === 0) && (
                      <tr><td colSpan={3} className="px-4 py-6 text-center text-gray-400">No events found in timeline.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
