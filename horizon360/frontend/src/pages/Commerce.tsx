import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';

export const Commerce = () => {
  const [products, setProducts] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      horizonApi.getProducts(),
      horizonApi.getOrders()
    ]).then(([prodData, orderData]) => {
      setProducts(prodData);
      setOrders(orderData);
      setLoading(false);
    }).catch(console.error);
  }, []);

  const totalProducts = products.length;
  const totalOrders = orders.length;
  const pendingOrders = orders.filter(o => o.status === 'draft' || o.status === 'confirmed').length;
  const revenue = orders.filter(o => o.status === 'fulfilled').reduce((sum, o) => sum + parseFloat(o.total_amount || 0), 0);

  return (
    <div className="flex-1 p-8 bg-gray-50 h-full overflow-y-auto">
      <div className="max-w-6xl w-full">
        <h2 className="text-3xl font-bold text-gray-900 mb-6">Commerce</h2>

        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Total Products</h3>
            <p className="text-2xl font-bold mt-2">{totalProducts}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Total Orders</h3>
            <p className="text-2xl font-bold mt-2">{totalOrders}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Pending Orders</h3>
            <p className="text-2xl font-bold mt-2 text-orange-600">{pendingOrders}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Fulfilled Revenue</h3>
            <p className="text-2xl font-bold mt-2 text-green-600">${revenue.toFixed(2)}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-8 mb-8">
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <h3 className="text-lg font-semibold">Products</h3>
            </div>
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr><td colSpan={3} className="px-6 py-4 text-center text-sm text-gray-500">Loading...</td></tr>
                ) : products.length === 0 ? (
                  <tr><td colSpan={3} className="px-6 py-4 text-center text-sm text-gray-500">No products found.</td></tr>
                ) : (
                  products.map((prod) => (
                    <tr key={prod.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{prod.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{prod.sku}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${prod.price}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <h3 className="text-lg font-semibold">Orders</h3>
            </div>
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Order ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr><td colSpan={3} className="px-6 py-4 text-center text-sm text-gray-500">Loading...</td></tr>
                ) : orders.length === 0 ? (
                  <tr><td colSpan={3} className="px-6 py-4 text-center text-sm text-gray-500">No orders found.</td></tr>
                ) : (
                  orders.map((ord) => (
                    <tr key={ord.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">#{ord.id}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${ord.total_amount}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          ord.status === 'fulfilled' ? 'bg-green-100 text-green-800' :
                          ord.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                          ord.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {ord.status}
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
