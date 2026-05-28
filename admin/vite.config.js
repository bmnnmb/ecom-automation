import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // OMS 订单中台服务路由 → port 8005
      '/api/orders': {
        target: 'http://localhost:8005',
        changeOrigin: true,
      },
      '/api/inventory': {
        target: 'http://localhost:8005',
        changeOrigin: true,
      },
      '/api/tickets': {
        target: 'http://localhost:8005',
        changeOrigin: true,
      },
      // 商品管理服务路由 → port 8006
      '/api/products': {
        target: 'http://localhost:8006',
        changeOrigin: true,
      },
      '/api/categories': {
        target: 'http://localhost:8006',
        changeOrigin: true,
      },
      // API 网关其他路由 → port 8000
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
