import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';

export const Partner = () => {
  const [partners, setPartners] = useState<any[]>([]);
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      horizonApi.getPartners(),
      horizonApi.getPartnerOpportunities()
    ]).then(([partnerData, oppData]) => {
      setPartners(partnerData);
      setOpportunities(oppData);
      setLoading(false);
    }).catch(console.error);
  }, []);

  const activePartners = partners.filter(p => p.status === 'active').length;
  const partnerPipeline = opportunities.filter(o => o.stage === 'open').reduce((sum, o) => sum + parseFloat(o.value || 0), 0);
  const partnerRevenue = opportunities.filter(o => o.stage === 'won').reduce((sum, o) => sum + parseFloat(o.value || 0), 0);
  const openOpportunities = opportunities.filter(o => o.stage === 'open').length;

  return (
    <div className="flex-1 p-8 bg-gray-50 h-full overflow-y-auto">
      <div className="max-w-6xl w-full">
        <h2 className="text-3xl font-bold text-gray-900 mb-6">Partner Management</h2>

        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Active Partners</h3>
            <p className="text-2xl font-bold mt-2">{activePartners}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Partner Pipeline</h3>
            <p className="text-2xl font-bold mt-2 text-blue-600">${partnerPipeline.toFixed(2)}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Partner Revenue</h3>
            <p className="text-2xl font-bold mt-2 text-green-600">${partnerRevenue.toFixed(2)}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Open Opportunities</h3>
            <p className="text-2xl font-bold mt-2 text-orange-600">{openOpportunities}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-8 mb-8">
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <h3 className="text-lg font-semibold">Partners</h3>
            </div>
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr><td colSpan={3} className="px-6 py-4 text-center text-sm text-gray-500">Loading...</td></tr>
                ) : partners.length === 0 ? (
                  <tr><td colSpan={3} className="px-6 py-4 text-center text-sm text-gray-500">No partners found.</td></tr>
                ) : (
                  partners.map((p) => (
                    <tr key={p.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{p.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{p.type}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          p.status === 'active' ? 'bg-green-100 text-green-800' :
                          p.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {p.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <h3 className="text-lg font-semibold">Opportunities</h3>
            </div>
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stage</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr><td colSpan={3} className="px-6 py-4 text-center text-sm text-gray-500">Loading...</td></tr>
                ) : opportunities.length === 0 ? (
                  <tr><td colSpan={3} className="px-6 py-4 text-center text-sm text-gray-500">No opportunities found.</td></tr>
                ) : (
                  opportunities.map((opp) => (
                    <tr key={opp.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{opp.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${opp.value}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          opp.stage === 'won' ? 'bg-green-100 text-green-800' :
                          opp.stage === 'lost' ? 'bg-red-100 text-red-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {opp.stage}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
