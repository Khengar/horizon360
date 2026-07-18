import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Login } from './pages/Login';
import "./App.css";

// Protected Route Wrapper
const ProtectedRoute = ({ isAuthenticated, children }: { isAuthenticated: boolean, children: JSX.Element }) => {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

const Placeholder = ({ title }: { title: string }) => (
  <div className="flex-1 flex flex-col h-full bg-white items-center justify-center p-8">
    <div className="bg-gray-50 rounded-xl p-12 text-center border border-gray-200">
      <h2 className="text-3xl font-bold text-gray-400 mb-2">{title}</h2>
      <p className="text-gray-500 max-w-sm mx-auto mt-4">This module is currently in development and will be available in the next major release.</p>
    </div>
  </div>
);

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    // Check if token exists on mount
    const token = localStorage.getItem('jwt_token');
    if (token) {
      setIsAuthenticated(true);
    }
    setIsInitializing(false);
  }, []);

  if (isInitializing) {
    return null; // or a loading spinner
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={
          isAuthenticated ? <Navigate to="/" replace /> : <Login onLogin={() => setIsAuthenticated(true)} />
        } />
        
        {/* Protected Dashboard Layout */}
        <Route path="/*" element={
          <ProtectedRoute isAuthenticated={isAuthenticated}>
            <div className="flex h-screen bg-[#f9fafb] overflow-hidden font-sans">
              <Sidebar />
              <main className="flex-1 overflow-y-auto">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/data-hub" element={<Placeholder title="Data Hub" />} />
                  <Route path="/sources" element={<Placeholder title="Connect Sources" />} />
                  <Route path="/identity" element={<Placeholder title="Identity Resolution Engine" />} />
                  <Route path="/profiles" element={<Dashboard />} />
                  <Route path="*" element={<Placeholder title="Not Found" />} />
                </Routes>
              </main>
            </div>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
