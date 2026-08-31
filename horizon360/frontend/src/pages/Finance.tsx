import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';

export const Finance = () => {
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    horizonApi.getInvoices().then(data => {
      setInvoices(data);
      setLoading(false);
    }).catch(console.error);
  }, []);

  const totalInvoices = invoices.length;
  const outstanding = invoices.filter(i => ['draft', 'requested', 'issued', 'overdue'].includes(i.status))
    .reduce((sum, i) => sum + parseFloat(i.amount || 0), 0);
  const paid = invoices.filter(i => i.status === 'paid')
    .reduce((sum, i) => sum + parseFloat(i.amount || 0), 0);
  const overdueCount = invoices.filter(i => i.status === 'overdue').length;

  return (
    <div className="flex-1 p-8 bg-gray-50 h-full overflow-y-auto">
      <div className="max-w-6xl w-full">
        <h2 className="text-3xl font-bold text-gray-900 mb-6">Finance</h2>

        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Outstanding</h3>
            <p className="text-2xl font-bold mt-2">${outstanding.toFixed(2)}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Paid Revenue</h3>
            <p className="text-2xl font-bold mt-2 text-green-600">${paid.toFixed(2)}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Overdue</h3>
            <p className="text-2xl font-bold mt-2 text-red-600">{overdueCount} Invoices</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Total Invoices</h3>
            <p className="text-2xl font-bold mt-2">{totalInvoices}</p>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Invoice #</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Deal</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Due Date</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr><td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500">Loading...</td></tr>
              ) : invoices.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500">No invoices found.</td></tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => alert(`Viewing details for ${inv.invoice_number}`)}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-brand-600">{inv.invoice_number}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Customer {inv.customer}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{inv.deal ? `Deal ${inv.deal}` : '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${parseFloat(inv.amount).toFixed(2)}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        inv.status === 'paid' ? 'bg-green-100 text-green-800' :
                        inv.status === 'overdue' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {inv.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{inv.due_date || '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
