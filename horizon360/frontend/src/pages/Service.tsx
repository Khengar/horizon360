import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';
import { ShieldCheck, ShieldAlert, Star, RefreshCcw, Filter } from 'lucide-react';

export const Service = () => {
  const [view, setView] = useState<'tickets' | 'warranties'>('tickets');
  const [tickets, setTickets] = useState<any[]>([]);
  const [entitlements, setEntitlements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Star analyzer filter state
  const [ratingFilter, setRatingFilter] = useState<string>('all');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      horizonApi.getServiceTickets().catch(() => []),
      horizonApi.getServiceEntitlements().catch(() => [])
    ]).then(([ticketsData, entitlementsData]) => {
      setTickets(ticketsData);
      setEntitlements(entitlementsData);
      setLoading(false);
    });
  }, []);

  const openCount = tickets.filter(t => t.status === 'open' || t.status === 'in_progress').length;
  const criticalCount = tickets.filter(t => t.priority === 'critical' && t.status !== 'resolved' && t.status !== 'closed').length;
  const resolvedCount = tickets.filter(t => t.status === 'resolved' || t.status === 'closed').length;
  const slaRisk = criticalCount; // Approximation for demo

  // Dynamic filtering based on star analyzer
  const filteredEntitlements = entitlements.filter(e => {
    if (ratingFilter === 'all') return true;
    if (ratingFilter === 'unrated') return e.feedback_rating == null;
    
    const r = e.feedback_rating;
    if (r == null) return false;

    if (ratingFilter.endsWith('+')) {
      const min = parseInt(ratingFilter.slice(0, -1));
      return r >= min;
    } else {
      return r === parseInt(ratingFilter);
    }
  });

  const totalReturns = filteredEntitlements.filter(e => e.return_issued).length;

  const renderStars = (rating: number | null) => {
    if (rating == null) return <span className="text-gray-400 italic">N/A</span>;
    return (
      <div className="flex items-center">
        {[...Array(5)].map((_, i) => (
          <Star key={i} className={`w-4 h-4 ${i < rating ? 'text-yellow-400 fill-current' : 'text-gray-300'}`} />
        ))}
      </div>
    );
  };

  const getGuaranteeStatus = (endDate: string) => {
    if (!endDate) return false;
    return new Date() < new Date(endDate);
  };

  return (
    <div className="flex-1 p-8 bg-gray-50 h-full overflow-y-auto">
      <div className="max-w-6xl w-full mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-3xl font-bold text-gray-900">Service & Support</h2>
          
          <div className="flex items-center bg-white p-1 rounded-lg border border-gray-200 shadow-sm">
            <button 
              onClick={() => setView('tickets')}
              className={`px-4 py-2 text-sm font-semibold rounded-md ${view === 'tickets' ? 'bg-indigo-50 text-indigo-700' : 'text-gray-500 hover:text-gray-700'}`}>
              Support Tickets
            </button>
            <button 
              onClick={() => setView('warranties')}
              className={`px-4 py-2 text-sm font-semibold rounded-md ${view === 'warranties' ? 'bg-brand-50 text-brand-700' : 'text-gray-500 hover:text-gray-700'}`}>
              Warranties & Feedback
            </button>
          </div>
        </div>

        {view === 'tickets' ? (
          <>
            <div className="grid grid-cols-4 gap-4 mb-8">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-sm font-medium text-gray-500">Open Tickets</h3>
                <p className="text-2xl font-bold mt-2">{openCount}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-sm font-medium text-gray-500">Critical Tickets</h3>
                <p className="text-2xl font-bold mt-2 text-red-600">{criticalCount}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-sm font-medium text-gray-500">SLA Risk</h3>
                <p className="text-2xl font-bold mt-2 text-orange-600">{slaRisk}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-sm font-medium text-gray-500">Resolved</h3>
                <p className="text-2xl font-bold mt-2 text-green-600">{resolvedCount}</p>
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ticket</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {loading ? (
                    <tr><td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">Loading...</td></tr>
                  ) : tickets.length === 0 ? (
                    <tr><td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">No tickets found.</td></tr>
                  ) : (
                    tickets.map((ticket) => (
                      <tr key={ticket.id} className="hover:bg-gray-50 cursor-pointer">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-brand-600">{ticket.title}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Customer {ticket.customer}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            ticket.priority === 'critical' ? 'bg-red-100 text-red-800' :
                            ticket.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {ticket.priority}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            ticket.status === 'resolved' || ticket.status === 'closed' ? 'bg-green-100 text-green-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {ticket.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(ticket.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-4 mb-6">
              
              {/* Star Analyzer Component */}
              <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-200 flex flex-col justify-center">
                <div className="flex items-center gap-2 mb-3">
                  <Filter className="w-4 h-4 text-gray-400" />
                  <h3 className="text-sm font-medium text-gray-600 uppercase tracking-wide">Star Analyzer Filter</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button onClick={() => setRatingFilter('all')} className={`px-3 py-1 text-sm font-medium rounded-full border ${ratingFilter === 'all' ? 'bg-brand-600 text-white border-brand-600' : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100'}`}>All</button>
                  <button onClick={() => setRatingFilter('5')} className={`px-3 py-1 text-sm font-medium rounded-full border flex items-center gap-1 ${ratingFilter === '5' ? 'bg-brand-600 text-white border-brand-600' : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100'}`}>5 <Star className="w-3 h-3" /></button>
                  <button onClick={() => setRatingFilter('4')} className={`px-3 py-1 text-sm font-medium rounded-full border flex items-center gap-1 ${ratingFilter === '4' ? 'bg-brand-600 text-white border-brand-600' : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100'}`}>4 <Star className="w-3 h-3" /></button>
                  <button onClick={() => setRatingFilter('3')} className={`px-3 py-1 text-sm font-medium rounded-full border flex items-center gap-1 ${ratingFilter === '3' ? 'bg-brand-600 text-white border-brand-600' : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100'}`}>3 <Star className="w-3 h-3" /></button>
                  <button onClick={() => setRatingFilter('2')} className={`px-3 py-1 text-sm font-medium rounded-full border flex items-center gap-1 ${ratingFilter === '2' ? 'bg-brand-600 text-white border-brand-600' : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100'}`}>2 <Star className="w-3 h-3" /></button>
                  <button onClick={() => setRatingFilter('1')} className={`px-3 py-1 text-sm font-medium rounded-full border flex items-center gap-1 ${ratingFilter === '1' ? 'bg-brand-600 text-white border-brand-600' : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100'}`}>1 <Star className="w-3 h-3" /></button>
                  <div className="w-px h-6 bg-gray-300 mx-1"></div>
                  <button onClick={() => setRatingFilter('4+')} className={`px-3 py-1 text-sm font-medium rounded-full border flex items-center gap-1 ${ratingFilter === '4+' ? 'bg-brand-600 text-white border-brand-600' : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100'}`}>4+ <Star className="w-3 h-3" /></button>
                  <button onClick={() => setRatingFilter('3+')} className={`px-3 py-1 text-sm font-medium rounded-full border flex items-center gap-1 ${ratingFilter === '3+' ? 'bg-brand-600 text-white border-brand-600' : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100'}`}>3+ <Star className="w-3 h-3" /></button>
                  <button onClick={() => setRatingFilter('unrated')} className={`px-3 py-1 text-sm font-medium rounded-full border ${ratingFilter === 'unrated' ? 'bg-brand-600 text-white border-brand-600' : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100'}`}>Unrated</button>
                </div>
              </div>

              {/* Retained Return Metric */}
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 flex flex-col justify-center">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Returns Processed (Filtered)</h3>
                <p className="text-3xl font-bold mt-2 text-rose-600">{totalReturns}</p>
                <p className="text-xs text-gray-400 mt-1">Based on current star filter</p>
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Purchase Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Feedback</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Guarantee Period</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Return Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {loading ? (
                      <tr><td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500">Loading entitlements...</td></tr>
                    ) : filteredEntitlements.length === 0 ? (
                      <tr><td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500">No purchase records match this rating filter.</td></tr>
                    ) : (
                      filteredEntitlements.map((ent) => {
                        const isGuaranteeActive = getGuaranteeStatus(ent.guarantee_end_date);
                        return (
                        <tr key={ent.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">{ent.customer_name}</div>
                            <div className="text-xs text-gray-500">ID: {ent.customer}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">{ent.product_name}</div>
                            <div className="text-xs text-gray-500 font-mono">{ent.product_id}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(ent.purchase_date).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4">
                            <div className="mb-1">{renderStars(ent.feedback_rating)}</div>
                            <div className="text-xs text-gray-500 truncate max-w-[200px]" title={ent.feedback_text}>
                              {ent.feedback_text || ''}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold">
                            {/* Compute on read: red if inactive, green if active */}
                            <div className={`flex items-center gap-1.5 ${isGuaranteeActive ? 'text-green-600' : 'text-red-600'}`}>
                              {isGuaranteeActive ? <ShieldCheck className="w-4 h-4" /> : <ShieldAlert className="w-4 h-4" />}
                              {ent.guarantee_period}
                            </div>
                            <div className="text-xs text-gray-400 font-normal mt-0.5">
                                Exp: {new Date(ent.guarantee_end_date).toLocaleDateString()}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {ent.return_issued ? (
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-100 text-rose-800">
                                <RefreshCcw className="w-3 h-3" /> Returned
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                                No Return
                              </span>
                            )}
                          </td>
                        </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
