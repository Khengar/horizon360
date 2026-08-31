import React, { useEffect, useState } from 'react';
import { horizonApi } from '../api';

export const HRMS = () => {
  const [employees, setEmployees] = useState<any[]>([]);
  const [leaveRequests, setLeaveRequests] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      horizonApi.getEmployees(),
      horizonApi.getLeaveRequests(),
      horizonApi.getDepartments()
    ]).then(([empData, leaveData, deptData]) => {
      setEmployees(empData);
      setLeaveRequests(leaveData);
      setDepartments(deptData);
      setLoading(false);
    }).catch(console.error);
  }, []);

  const totalEmployees = employees.length;
  const activeEmployees = employees.filter(e => e.status === 'active').length;
  const pendingLeave = leaveRequests.filter(l => l.status === 'pending').length;
  const totalDepartments = departments.length;

  return (
    <div className="flex-1 p-8 bg-gray-50 h-full overflow-y-auto">
      <div className="max-w-6xl w-full">
        <h2 className="text-3xl font-bold text-gray-900 mb-6">HRMS</h2>

        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Total Employees</h3>
            <p className="text-2xl font-bold mt-2">{totalEmployees}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Active</h3>
            <p className="text-2xl font-bold mt-2 text-green-600">{activeEmployees}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Pending Leave</h3>
            <p className="text-2xl font-bold mt-2 text-orange-600">{pendingLeave}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-sm font-medium text-gray-500">Departments</h3>
            <p className="text-2xl font-bold mt-2 text-blue-600">{totalDepartments}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-8 mb-8">
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <h3 className="text-lg font-semibold">Employees</h3>
            </div>
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr><td colSpan={3} className="px-6 py-4 text-center text-sm text-gray-500">Loading...</td></tr>
                ) : employees.length === 0 ? (
                  <tr><td colSpan={3} className="px-6 py-4 text-center text-sm text-gray-500">No employees found.</td></tr>
                ) : (
                  employees.map((emp) => (
                    <tr key={emp.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{emp.first_name} {emp.last_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{emp.role}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          emp.status === 'active' ? 'bg-green-100 text-green-800' :
                          emp.status === 'on_leave' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {emp.status}
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
              <h3 className="text-lg font-semibold">Leave Requests</h3>
            </div>
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Employee ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dates</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr><td colSpan={3} className="px-6 py-4 text-center text-sm text-gray-500">Loading...</td></tr>
                ) : leaveRequests.length === 0 ? (
                  <tr><td colSpan={3} className="px-6 py-4 text-center text-sm text-gray-500">No leave requests found.</td></tr>
                ) : (
                  leaveRequests.map((req) => (
                    <tr key={req.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Emp #{req.employee}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{req.start_date} to {req.end_date}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          req.status === 'approved' ? 'bg-green-100 text-green-800' :
                          req.status === 'pending' ? 'bg-orange-100 text-orange-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {req.status}
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
