import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Database, Link, UserCheck, Users, LogOut, HelpCircle, Settings } from 'lucide-react';

export const Sidebar = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('company_api_token');
    navigate('/login');
  };

  const navItems = [
    { name: 'Overview', path: '/', icon: LayoutDashboard },
    { name: 'Data Hub', path: '/data-hub', icon: Database },
    { name: 'Sources', path: '/sources', icon: Link },
    { name: 'Identity Resolution', path: '/identity', icon: UserCheck },
    { name: 'Unified Profiles', path: '/profiles', icon: Users },
  ];

  return (
    <div className="w-64 bg-[#f8fafc] border-r border-gray-200 h-screen flex flex-col">
      <div className="p-6">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-brand-600 rounded grid place-items-center">
            <div className="w-3 h-3 bg-white rounded-sm" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900 leading-tight">Horizon 360</h1>
            <p className="text-[10px] text-gray-500 uppercase tracking-wide">Enterprise SaaS</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 space-y-1 mt-4">
        {navItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                isActive
                  ? 'bg-brand-50 text-brand-600 border-l-4 border-brand-600'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 border-l-4 border-transparent'
              }`
            }
          >
            <item.icon className="w-4 h-4 mr-3" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 space-y-1">
        <NavLink 
          to="/settings" 
          className={({ isActive }) => `flex items-center w-full px-3 py-2 text-sm font-medium rounded-md transition-colors ${isActive ? 'bg-brand-50 text-brand-600 border-l-4 border-brand-600' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 border-l-4 border-transparent'}`}
        >
          <Settings className="w-4 h-4 mr-3" /> Settings
        </NavLink>
        <button className="flex items-center w-full px-3 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-100 cursor-pointer">
          <HelpCircle className="w-4 h-4 mr-3" /> Support
        </button>
        <button onClick={handleLogout} className="flex items-center w-full px-3 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-100 cursor-pointer text-red-600 hover:text-red-700">
          <LogOut className="w-4 h-4 mr-3" /> Logout
        </button>
      </div>
    </div>
  );
};
