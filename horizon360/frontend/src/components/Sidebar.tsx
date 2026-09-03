import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Database, Link, UserCheck, Users, LogOut, HelpCircle, Settings, Share2, Map, Network } from 'lucide-react';

export const Sidebar = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('company_api_token');
    navigate('/login');
  };

  const [isBiomsOpen, setIsBiomsOpen] = React.useState(true);

  const topNav = [
    { name: 'Operations Map', path: '/map', icon: Map },
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Customers', path: '/profiles', icon: Users },
  ];

  const biomNav = [
    { name: 'Sales', path: '/pipeline', icon: LayoutDashboard, comingSoon: false },
    { name: 'Finance', path: '/finance', icon: Database, comingSoon: false },
    { name: 'Service', path: '/service', icon: UserCheck, comingSoon: false },
    { name: 'Marketing', path: '/marketing', icon: Users, comingSoon: false },
    { name: 'Projects', path: '/projects', icon: LayoutDashboard, comingSoon: false },
    { name: 'HRMS', path: '/hrms', icon: Users, comingSoon: false },
    { name: 'Partner', path: '/partner', icon: Link, comingSoon: false },
    { name: 'Vendor', path: '/vendor', icon: Link, comingSoon: false },
  ];

  const bottomNav = [
    { name: 'Intelligence', path: '/intelligence', icon: Database },
    { name: 'Workflows', path: '/workflows', icon: Share2 },
    { name: 'Integrations', path: '/integrations', icon: Network },
    { name: 'Data Hub', path: '/data-hub', icon: Database },
    { name: 'Sources', path: '/sources', icon: Link },
    { name: 'Identity Resolution', path: '/identity', icon: UserCheck },
  ];

  return (
    <div className="w-64 bg-[#f8fafc] border-r border-gray-200 h-screen flex flex-col overflow-hidden">
      <div className="p-6 shrink-0">
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

      <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-6">
        <nav className="space-y-1">
          {topNav.map((item) => (
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

        <div>
          <button 
            onClick={() => setIsBiomsOpen(!isBiomsOpen)}
            className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider hover:text-gray-600 cursor-pointer"
          >
            <span>BIOMs</span>
            <span>{isBiomsOpen ? '▾' : '▸'}</span>
          </button>
          
          {isBiomsOpen && (
            <nav className="mt-2 space-y-1">
              {biomNav.map((item) => {
                if (item.comingSoon) {
                  return (
                    <div key={item.name} className="flex items-center justify-between px-3 py-2 text-sm font-medium text-gray-400 cursor-not-allowed border-l-4 border-transparent">
                      <div className="flex items-center">
                        <item.icon className="w-4 h-4 mr-3 opacity-50" />
                        {item.name}
                      </div>
                      <span className="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">Coming Soon</span>
                    </div>
                  );
                }
                
                return (
                  <NavLink
                    key={item.name}
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center justify-between px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive
                          ? 'bg-brand-50 text-brand-600 border-l-4 border-brand-600'
                          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 border-l-4 border-transparent'
                      }`
                    }
                  >
                    <div className="flex items-center">
                      <item.icon className="w-4 h-4 mr-3" />
                      {item.name}
                    </div>
                  </NavLink>
                );
              })}
            </nav>
          )}
        </div>

        <nav className="space-y-1">
          {bottomNav.map((item) => (
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
      </div>

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
