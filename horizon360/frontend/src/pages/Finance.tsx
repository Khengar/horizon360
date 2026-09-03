import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';
import { Download, ToggleLeft, ToggleRight, DollarSign } from 'lucide-react';

export const Finance = () => {
  const [view, setView] = useState<'customer' | 'company'>('customer');
  const [invoices, setInvoices] = useState<any[]>([]);
  const [expenses, setExpenses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    if (view === 'customer') {
      horizonApi.getInvoices().then(data => {
        setInvoices(data);
        setLoading(false);
      }).catch(console.error);
    } else {
      horizonApi.getExpenses().then(data => {
        setExpenses(data);
        setLoading(false);
      }).catch(console.error);
    }
  }, [view]);

  const handleDownloadInvoice = (inv: any, e: React.MouseEvent) => {
    e.stopPropagation();
    // Simulate generating and downloading an invoice PDF with unique order/invoice id
    const invoiceContent = `INVOICE\n\nID: ${inv.id}\nInvoice #: ${inv.invoice_number}\nAmount: ${inv.amount}\nStatus: ${inv.status}\nCustomer ID: ${inv.customer}\nDeal ID: ${inv.deal || 'N/A'}`;
    const blob = new Blob([invoiceContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `invoice_${inv.invoice_number}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadExpenseReceipt = (exp: any, e: React.MouseEvent) => {
    e.stopPropagation();
    const receiptContent = `EXPENSE RECEIPT\n\nID: ${exp.id}\nDescription: ${exp.description}\nAmount: ${exp.amount}\nStatus: ${exp.status}`;
    const blob = new Blob([receiptContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `expense_${exp.id.split('-')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Metrics calculation
  const totalInvoices = invoices.length;
  const outstanding = invoices.filter(i => ['draft', 'requested', 'issued', 'overdue'].includes(i.status))
    .reduce((sum, i) => sum + parseFloat(i.amount || 0), 0);
  const paid = invoices.filter(i => i.status === 'paid')
    .reduce((sum, i) => sum + parseFloat(i.amount || 0), 0);
  const overdueCount = invoices.filter(i => i.status === 'overdue').length;

  const totalExpenses = expenses.length;
  const pendingExpenses = expenses.filter(e => e.status === 'pending')
    .reduce((sum, e) => sum + parseFloat(e.amount || 0), 0);
  const paidExpenses = expenses.filter(e => e.status === 'paid')
    .reduce((sum, e) => sum + parseFloat(e.amount || 0), 0);

  return (
    <div className="flex-1 p-8 bg-gray-50 h-full overflow-y-auto">
      <div className="max-w-6xl w-full">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-3xl font-bold text-gray-900">Finance</h2>
          
          <div className="flex items-center space-x-3 bg-white p-2 rounded-lg border border-gray-200 shadow-sm cursor-pointer" onClick={() => setView(view === 'customer' ? 'company' : 'customer')}>
            <span className={`text-sm font-semibold ${view === 'customer' ? 'text-indigo-600' : 'text-gray-400'}`}>Customer Base (AR)</span>
            {view === 'customer' ? (
              <ToggleLeft className="w-8 h-8 text-indigo-600" />
            ) : (
              <ToggleRight className="w-8 h-8 text-brand-600" />
            )}
            <span className={`text-sm font-semibold ${view === 'company' ? 'text-brand-600' : 'text-gray-400'}`}>Company Finances (AP)</span>
          </div>
        </div>

        {view === 'customer' ? (
          <>
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
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {loading ? (
                    <tr><td colSpan={7} className="px-6 py-4 text-center text-sm text-gray-500">Loading...</td></tr>
                  ) : invoices.length === 0 ? (
                    <tr><td colSpan={7} className="px-6 py-4 text-center text-sm text-gray-500">No invoices found.</td></tr>
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
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button onClick={(e) => handleDownloadInvoice(inv, e)} className="text-gray-400 hover:text-indigo-600 transition-colors" title="Download Invoice">
                            <Download className="w-5 h-5 inline" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <>
            <div className="grid grid-cols-3 gap-4 mb-8">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-sm font-medium text-gray-500">Pending Expenses</h3>
                <p className="text-2xl font-bold mt-2 text-yellow-600">${pendingExpenses.toFixed(2)}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-sm font-medium text-gray-500">Paid Expenses</h3>
                <p className="text-2xl font-bold mt-2 text-green-600">${paidExpenses.toFixed(2)}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-sm font-medium text-gray-500">Total Transactions</h3>
                <p className="text-2xl font-bold mt-2">{totalExpenses}</p>
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {loading ? (
                    <tr><td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500">Loading...</td></tr>
                  ) : expenses.length === 0 ? (
                    <tr><td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500">No company expenses found.</td></tr>
                  ) : (
                    expenses.map((exp) => (
                      <tr key={exp.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">{exp.id.split('-')[0]}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{exp.description}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${parseFloat(exp.amount).toFixed(2)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(exp.date).toLocaleDateString()}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            exp.status === 'paid' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {exp.status.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button onClick={(e) => handleDownloadExpenseReceipt(exp, e)} className="text-gray-400 hover:text-brand-600 transition-colors" title="Download Receipt">
                            <Download className="w-5 h-5 inline" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
