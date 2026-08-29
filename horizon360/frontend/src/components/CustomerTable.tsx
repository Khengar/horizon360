import React from 'react';
import { Link } from 'react-router-dom';

export const CustomerTable = ({ customers }: { customers: any[] }) => {
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
                   <Link 
                     to={`/customers/${c.id}/360`}
                     className="px-3 py-1 text-xs font-medium text-brand-600 bg-brand-50 border border-brand-200 rounded hover:bg-brand-100 transition-colors cursor-pointer inline-block"
                   >
                     View Profile
                   </Link>
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
    </div>
  );
};
