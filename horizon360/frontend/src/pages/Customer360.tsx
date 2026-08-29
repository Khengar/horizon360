import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { horizonApi } from '../api';
import { StatCard } from '../components/StatCard';

export const Customer360 = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      horizonApi.getCustomer360(id)
        .then(res => {
          setData(res);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          setLoading(false);
        });
    }
  }, [id]);

  if (loading) return <div className="p-8">Loading Customer 360...</div>;
  if (!data) return <div className="p-8">Customer not found.</div>;

  const { identity, company, contact, deals, aggregates, timeline } = data;

  return (
    <div className="flex-1 flex flex-col h-full bg-[#f9fafb]">
      <header className="h-16 border-b border-gray-200 bg-white flex items-center px-8 shadow-sm">
        <Link to="/" className="text-brand-600 hover:text-brand-800 mr-4 font-medium">
          &larr; Back to Directory
        </Link>
        <h1 className="text-xl font-bold text-gray-900">
          Customer 360
        </h1>
      </header>

      <div className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-6xl mx-auto space-y-6">
          
          {/* Header Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {identity.primary_email || identity.primary_phone || 'Anonymous User'}
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Customer ID: <span className="font-mono bg-gray-100 px-1 rounded">{identity.id}</span>
              </p>
              <p className="text-sm text-gray-500">Company: {company.name}</p>
            </div>
            {contact && (
              <div className="text-right">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  CRM Contact Linked
                </span>
                <p className="text-xs text-gray-400 mt-1">Contact ID: {contact.id}</p>
              </div>
            )}
          </div>

          {/* Aggregates */}
          <div className="grid grid-cols-4 gap-4">
            <StatCard title="Total Deal Value" value={`$${aggregates.total_deal_value.toFixed(2)}`} subtext="" />
            <StatCard title="Open Pipeline" value={`$${aggregates.open_pipeline_value.toFixed(2)}`} subtext={`${aggregates.open_deals_count} open deals`} />
            <StatCard title="Won Revenue" value={`$${aggregates.won_revenue.toFixed(2)}`} subtext={`${aggregates.won_deals_count} won deals`} isPositive />
            <StatCard title="Lost Deals" value={aggregates.lost_deals_count.toString()} subtext="Closed lost" />
          </div>

          <div className="grid grid-cols-2 gap-6">
            {/* Deals */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col h-[500px]">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Deals</h3>
              </div>
              <div className="flex-1 overflow-y-auto p-0">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {deals.length === 0 ? (
                      <tr>
                        <td colSpan={3} className="px-6 py-8 text-center text-gray-500">No deals found.</td>
                      </tr>
                    ) : (
                      deals.map((deal: any) => (
                        <tr key={deal.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${deal.stage === 'won' ? 'bg-green-100 text-green-800' : deal.stage === 'lost' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}`}>
                              {deal.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${parseFloat(deal.value).toFixed(2)}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(deal.created_at).toLocaleDateString()}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Timeline */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col h-[500px]">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Event Timeline</h3>
              </div>
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {timeline.length === 0 ? (
                  <p className="text-center text-gray-500 mt-10">No events in timeline.</p>
                ) : (
                  timeline.map((event: any, index: number) => (
                    <div key={event.id || index} className="relative pl-6 border-l-2 border-brand-200">
                      <div className="absolute w-3 h-3 bg-brand-500 rounded-full -left-[7px] top-1.5 border-2 border-white"></div>
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-semibold text-brand-700">{event.event_name}</span>
                        <span className="text-xs text-gray-400">{new Date(event.created_at).toLocaleString()}</span>
                      </div>
                      <div className="text-sm text-gray-600 bg-gray-50 p-2 rounded border border-gray-100 overflow-x-auto">
                        <pre className="text-xs">{JSON.stringify(event.payload, null, 2)}</pre>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
