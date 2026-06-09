import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import AdminLayout from '../layout/AdminLayout';
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';
import Orders from '../pages/Orders';
import CustomerService from '../pages/CustomerService';
import Products from '../pages/Products';
import Competitors from '../pages/Competitors';
import Marketing from '../pages/Marketing';
import System from '../pages/System';
import Analytics from '../pages/Analytics';
import SupplyChain from '../pages/SupplyChain';
import Customers from '../pages/Customers';
import Finance from '../pages/Finance';
import Settings from '../pages/Settings';

// 路由守卫：检查登录状态
function AuthGuard({ children }) {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/',
    element: (
      <AuthGuard>
        <AdminLayout />
      </AuthGuard>
    ),
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'products', element: <Products /> },
      { path: 'orders', element: <Orders /> },
      { path: 'customers', element: <Customers /> },
      { path: 'marketing', element: <Marketing /> },
      { path: 'analytics', element: <Analytics /> },
      { path: 'service', element: <CustomerService /> },
      { path: 'finance', element: <Finance /> },
      { path: 'supply-chain', element: <SupplyChain /> },
      { path: 'competitors', element: <Competitors /> },
      { path: 'system', element: <System /> },
      { path: 'settings', element: <Settings /> },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
]);

export default router;
