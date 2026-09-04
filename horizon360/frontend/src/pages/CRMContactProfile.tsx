import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { horizonApi } from '../api';
import { Mail, Phone, Calendar, CheckSquare, Edit, MessageSquare } from 'lucide-react';

export const CRMContactProfile = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Reusing getCustomer360 for mockup purposes, but this represents
  // the CRM-only view (HubSpot style) of a contact.
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

  if (loading) return <div className="p-8">Loading CRM Contact...</div>;
  if (!data) return <div className="p-8">Contact not found.</div>;

  const { identity, company, deals } = data;

  return (
    <div className="flex-1 flex flex-col h-full bg-[#f9fafb]">
      <header className="h-16 border-b border-gray-200 bg-white flex items-center px-8 shadow-sm">
        <Link to="/crm/customers" className="text-brand-600 hover:text-brand-800 mr-4 font-medium text-sm">
          &larr; Back to Contacts
        </Link>
        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-3">
          {identity.primary_email || identity.primary_phone || 'Unnamed Contact'}
          <span className="text-xs font-normal px-2 py-1 bg-blue-100 text-blue-800 rounded-full">CRM Contact</span>
        </h1>
      </header>

      <div className="flex-1 p-6 overflow-y-auto">
        <div className="max-w-7xl mx-auto flex gap-6 h-full">
          
          {/* Left Column: About Section (HubSpot style) */}
          <div className="w-1/3 flex flex-col gap-4">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold text-gray-900">About this contact</h3>
                <button className="text-gray-400 hover:text-brand-600"><Edit className="w-4 h-4"/></button>
              </div>
              <div className="space-y-4 text-sm">
                <div>
                  <label className="text-gray-500 text-xs">Email</label>
                  <p className="text-gray-900">{identity.primary_email || '--'}</p>
                </div>
                <div>
                  <label className="text-gray-500 text-xs">Phone Number</label>
                  <p className="text-gray-900">{identity.primary_phone || '--'}</p>
                </div>
                <div>
                  <label className="text-gray-500 text-xs">Lifecycle Stage</label>
                  <p className="text-gray-900">Lead</p>
                </div>
                <div>
                  <label className="text-gray-500 text-xs">Contact Owner</label>
                  <p className="text-gray-900">System Admin</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
              <h3 className="font-semibold text-gray-900 mb-4">Company</h3>
              <div className="text-sm">
                <Link to="#" className="text-brand-600 hover:underline">{company.name || 'Unknown Company'}</Link>
                <p className="text-gray-500 text-xs mt-1">Industry: {company.industry || '--'}</p>
              </div>
            </div>
          </div>

          {/* Middle Column: Activity Timeline */}
          <div className="w-1/2 flex flex-col gap-4">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="flex border-b border-gray-200 bg-gray-50 rounded-t-lg">
                <button className="flex-1 py-3 text-sm font-medium text-brand-600 border-b-2 border-brand-600 flex justify-center items-center gap-2"><Edit className="w-4 h-4"/> Note</button>
                <button className="flex-1 py-3 text-sm font-medium text-gray-600 hover:bg-gray-100 flex justify-center items-center gap-2"><Mail className="w-4 h-4"/> Email</button>
                <button className="flex-1 py-3 text-sm font-medium text-gray-600 hover:bg-gray-100 flex justify-center items-center gap-2"><Phone className="w-4 h-4"/> Call</button>
                <button className="flex-1 py-3 text-sm font-medium text-gray-600 hover:bg-gray-100 flex justify-center items-center gap-2"><CheckSquare className="w-4 h-4"/> Task</button>
                <button className="flex-1 py-3 text-sm font-medium text-gray-600 hover:bg-gray-100 flex justify-center items-center gap-2"><Calendar className="w-4 h-4"/> Meeting</button>
              </div>
              <div className="p-4 bg-white">
                <textarea className="w-full border border-gray-300 rounded-md p-3 text-sm focus:outline-none focus:border-brand-500" rows={3} placeholder="Start typing to leave a note..."></textarea>
                <div className="mt-3 flex justify-end">
                  <button className="bg-brand-600 text-white px-4 py-2 rounded text-sm font-medium hover:bg-brand-700">Save note</button>
                </div>
              </div>
            </div>

            {/* Mocked CRM Activities */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 flex-1">
              <h3 className="font-semibold text-gray-900 mb-4">Activity</h3>
              <div className="space-y-6">
                <div className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 shrink-0">
                    <Mail className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">Email logged <span className="text-gray-500 font-normal">by System Admin</span></p>
                    <p className="text-xs text-gray-400 mt-0.5">Today 10:23 AM</p>
                    <div className="mt-2 text-sm text-gray-700 bg-gray-50 p-3 rounded border border-gray-100">
                      <strong>Subject: Introduction</strong><br/>
                      Hi there, checking in on the proposal...
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Associations */}
          <div className="w-1/4 flex flex-col gap-4">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold text-gray-900">Deals</h3>
                <button className="text-brand-600 text-sm font-medium hover:underline">+ Add</button>
              </div>
              {deals.length === 0 ? (
                <p className="text-sm text-gray-500">No deals associated.</p>
              ) : (
                <div className="space-y-3">
                  {deals.map((deal: any) => (
                    <div key={deal.id} className="text-sm border border-gray-100 p-3 rounded bg-gray-50">
                      <Link to="#" className="text-brand-600 font-medium hover:underline block">{deal.title}</Link>
                      <p className="text-gray-500 mt-1">${parseFloat(deal.value).toFixed(0)} • {deal.stage}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
