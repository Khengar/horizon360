import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';
import { Download, ToggleLeft, ToggleRight, DollarSign, Search, TrendingUp, TrendingDown, Activity, List, FileSpreadsheet } from 'lucide-react';

export const Finance = () => {
  const [view, setView] = useState<'customer' | 'company' | 'ledger'>('customer');
  const [invoices, setInvoices] = useState<any[]>([]);
  const [expenses, setExpenses] = useState<any[]>([]);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [newExpense, setNewExpense] = useState({ description: '', amount: '', status: 'pending' });

  // Pagination for transactions
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchData = async (currentPage = 1) => {
    setLoading(true);
    try {
      const [invData, expData, txData] = await Promise.all([
        horizonApi.getInvoices(),
        horizonApi.getExpenses(),
        horizonApi.getTransactions(currentPage).catch(() => ({ results: [], count: 0 }))
      ]);
      setInvoices(invData);
      setExpenses(expData);
      
      if (txData && txData.results) {
        setTransactions(txData.results);
        setTotalPages(Math.ceil(txData.count / 10) || 1);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(page);
  }, [page]);

  const handleExportCSV = () => {
    alert("Exporting selected range of transactions to CSV... (Dummy action)");
  };

  const handleCreateExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await horizonApi.createExpense({
        ...newExpense,
        amount: parseFloat(newExpense.amount)
      });
      setShowExpenseModal(false);
      setNewExpense({ description: '', amount: '', status: 'pending' });
      await fetchData(page);
    } catch (error) {
      console.error(error);
      alert('Failed to create expense');
    }
  };

  const handleDownloadInvoice = (inv: any, e: React.MouseEvent) => {
    e.stopPropagation();
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

  // Filtered Data
  const term = searchTerm.toLowerCase();
  const filteredInvoices = invoices.filter(inv => 
    inv.invoice_number?.toLowerCase().includes(term) ||
    inv.status?.toLowerCase().includes(term) ||
    String(inv.customer).includes(term)
  );
  
  const filteredExpenses = expenses.filter(exp =>
    exp.description?.toLowerCase().includes(term) ||
    exp.status?.toLowerCase().includes(term)
  );

  const filteredTransactions = transactions.filter(tx =>
    tx.description?.toLowerCase().includes(term) ||
    tx.transaction_type?.toLowerCase().includes(term)
  );

  // Global Metrics (based on ALL data, not just filtered)
  const totalEarned = invoices.filter(i => i.status === 'paid').reduce((sum, i) => sum + parseFloat(i.amount || 0), 0);
  const totalSpent = expenses.filter(e => e.status === 'paid').reduce((sum, e) => sum + parseFloat(e.amount || 0), 0);
  const netIncome = totalEarned - totalSpent;

  // View Specific Metrics (based on FILTERED data)
  const totalInvoices = filteredInvoices.length;
  const outstanding = filteredInvoices.filter(i => ['draft', 'requested', 'issued', 'overdue'].includes(i.status))
    .reduce((sum, i) => sum + parseFloat(i.amount || 0), 0);
  const paid = filteredInvoices.filter(i => i.status === 'paid')
    .reduce((sum, i) => sum + parseFloat(i.amount || 0), 0);

  const totalExpensesCount = filteredExpenses.length;
  const pendingExpenses = filteredExpenses.filter(e => e.status === 'pending')
    .reduce((sum, e) => sum + parseFloat(e.amount || 0), 0);
  const paidExpensesAmount = filteredExpenses.filter(e => e.status === 'paid')
    .reduce((sum, e) => sum + parseFloat(e.amount || 0), 0);

  return (
    <div className="flex-1 p-8 bg-gray-50 h-full overflow-y-auto">
      <div className="max-w-6xl w-full mx-auto">
        
        {/* Header with Search and Toggle */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-3xl font-bold text-gray-900">Finance</h2>
          
          <div className="flex items-center space-x-4">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-4 w-4 text-gray-400" />
              </div>
              <input
                type="text"
                className="pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-brand-500 focus:border-brand-500 w-64"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            
            <div className="flex items-center bg-white p-1 rounded-lg border border-gray-200 shadow-sm">
              <button 
                onClick={() => setView('customer')}
                className={`px-3 py-1.5 text-sm font-semibold rounded-md ${view === 'customer' ? 'bg-indigo-50 text-indigo-700' : 'text-gray-500 hover:text-gray-700'}`}>
                AR Invoices
              </button>
              <button 
                onClick={() => setView('company')}
                className={`px-3 py-1.5 text-sm font-semibold rounded-md ${view === 'company' ? 'bg-brand-50 text-brand-700' : 'text-gray-500 hover:text-gray-700'}`}>
                AP Expenses
              </button>
              <button 
                onClick={() => setView('ledger')}
                className={`px-3 py-1.5 text-sm font-semibold rounded-md ${view === 'ledger' ? 'bg-emerald-50 text-emerald-700' : 'text-gray-500 hover:text-gray-700'}`}>
                Ledger (Earn/Loss)
              </button>
            </div>
          </div>
        </div>

        {/* Global Financial Overview */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 p-6 rounded-lg shadow-sm border border-indigo-200">
            <div className="flex items-center gap-3 mb-2">
              <TrendingUp className="w-5 h-5 text-indigo-600" />
              <h3 className="text-sm font-semibold text-indigo-900">Total Earned (Paid AR)</h3>
            </div>
            <p className="text-3xl font-bold text-indigo-700">${totalEarned.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
          </div>
          
          <div className="bg-gradient-to-br from-rose-50 to-rose-100 p-6 rounded-lg shadow-sm border border-rose-200">
            <div className="flex items-center gap-3 mb-2">
              <TrendingDown className="w-5 h-5 text-rose-600" />
              <h3 className="text-sm font-semibold text-rose-900">Total Spent (Paid AP)</h3>
            </div>
            <p className="text-3xl font-bold text-rose-700">${totalSpent.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
          </div>

          <div className={`bg-gradient-to-br p-6 rounded-lg shadow-sm border ${netIncome >= 0 ? 'from-green-50 to-green-100 border-green-200' : 'from-red-50 to-red-100 border-red-200'}`}>
            <div className="flex items-center gap-3 mb-2">
              <Activity className={`w-5 h-5 ${netIncome >= 0 ? 'text-green-600' : 'text-red-600'}`} />
              <h3 className={`text-sm font-semibold ${netIncome >= 0 ? 'text-green-900' : 'text-red-900'}`}>Net Income</h3>
            </div>
            <p className={`text-3xl font-bold ${netIncome >= 0 ? 'text-green-700' : 'text-red-700'}`}>
              ${netIncome.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
            </p>
          </div>
        </div>

        {/* Dynamic Views */}
        {view === 'customer' && (
          <>
            <div className="grid grid-cols-3 gap-4 mb-8">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-sm font-medium text-gray-500">Outstanding Invoices</h3>
                <p className="text-2xl font-bold mt-2 text-indigo-600">${outstanding.toFixed(2)}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-sm font-medium text-gray-500">Paid Invoices (Filtered)</h3>
                <p className="text-2xl font-bold mt-2 text-green-600">${paid.toFixed(2)}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-sm font-medium text-gray-500">Count</h3>
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
                  ) : filteredInvoices.length === 0 ? (
                    <tr><td colSpan={7} className="px-6 py-4 text-center text-sm text-gray-500">No invoices found.</td></tr>
                  ) : (
                    filteredInvoices.map((inv) => (
                      <tr key={inv.id} className="hover:bg-gray-50">
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
        )}

        {view === 'company' && (
          <>
            <div className="flex justify-between items-center mb-6 mt-2">
              <h3 className="text-xl font-semibold text-gray-800">Company Expenses</h3>
              <button onClick={() => setShowExpenseModal(true)} className="bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg shadow font-medium text-sm transition-colors">
                + Add Expense
              </button>
            </div>
            
            <div className="grid grid-cols-3 gap-4 mb-8">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-sm font-medium text-gray-500">Pending Expenses</h3>
                <p className="text-2xl font-bold mt-2 text-yellow-600">${pendingExpenses.toFixed(2)}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-sm font-medium text-gray-500">Paid Expenses (Filtered)</h3>
                <p className="text-2xl font-bold mt-2 text-rose-600">${paidExpensesAmount.toFixed(2)}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-sm font-medium text-gray-500">Count</h3>
                <p className="text-2xl font-bold mt-2">{totalExpensesCount}</p>
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
                  ) : filteredExpenses.length === 0 ? (
                    <tr><td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500">No company expenses found.</td></tr>
                  ) : (
                    filteredExpenses.map((exp) => (
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

        {view === 'ledger' && (
          <>
            <div className="flex justify-between items-center mb-6 mt-2">
              <h3 className="text-xl font-semibold text-gray-800">Master Ledger</h3>
              <button onClick={handleExportCSV} className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg shadow font-medium text-sm transition-colors flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4" /> Export CSV (Range)
              </button>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden mb-4">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type (Earn/Loss)</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {loading ? (
                    <tr><td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500">Loading ledger...</td></tr>
                  ) : filteredTransactions.length === 0 ? (
                    <tr><td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500">No transactions recorded yet.</td></tr>
                  ) : (
                    filteredTransactions.map((tx) => (
                      <tr key={tx.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(tx.date).toLocaleDateString()}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            tx.transaction_type === 'earn' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {tx.transaction_type === 'earn' ? 'EARN (Credit)' : 'LOSS (Debit)'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{tx.description}</td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-bold text-right ${
                          tx.transaction_type === 'earn' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {tx.transaction_type === 'earn' ? '+' : '-'}${parseFloat(tx.amount).toFixed(2)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 bg-white border border-gray-200 rounded-lg">
                <div className="flex flex-1 justify-between sm:hidden">
                  <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">Previous</button>
                  <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">Next</button>
                </div>
                <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Showing page <span className="font-medium">{page}</span> of <span className="font-medium">{totalPages}</span>
                    </p>
                  </div>
                  <div>
                    <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                      <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50">
                        <span className="sr-only">Previous</span>
                        &larr;
                      </button>
                      <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50">
                        <span className="sr-only">Next</span>
                        &rarr;
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Expense Modal overlay */}
      {showExpenseModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900">Add Company Expense</h3>
              <button onClick={() => setShowExpenseModal(false)} className="text-gray-400 hover:text-gray-500">&times;</button>
            </div>
            <form onSubmit={handleCreateExpense} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <input required type="text" value={newExpense.description} onChange={e => setNewExpense({...newExpense, description: e.target.value})} className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-brand-500 focus:border-brand-500" placeholder="e.g. Office Supplies" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount</label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-gray-500">$</span>
                  <input required type="number" step="0.01" min="0" value={newExpense.amount} onChange={e => setNewExpense({...newExpense, amount: e.target.value})} className="w-full border border-gray-300 rounded-lg pl-7 pr-3 py-2 focus:ring-brand-500 focus:border-brand-500" placeholder="0.00" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select value={newExpense.status} onChange={e => setNewExpense({...newExpense, status: e.target.value})} className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-brand-500 focus:border-brand-500">
                  <option value="pending">Pending</option>
                  <option value="paid">Paid</option>
                </select>
              </div>
              <div className="pt-4 flex justify-end space-x-3">
                <button type="button" onClick={() => setShowExpenseModal(false)} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
                <button type="submit" className="px-4 py-2 text-sm font-medium text-white bg-brand-600 rounded-lg hover:bg-brand-700">Save Expense</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
