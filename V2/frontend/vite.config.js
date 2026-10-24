import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from 'node:url';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1', port: 5173, strictPort: true,
    proxy: { '/api': { target: process.env.SANCTUARY_BACKEND_URL || 'http://127.0.0.1:8000', changeOrigin: true, rewrite: path => path.replace(/^\/api/, '') } }
  },
  build: { rollupOptions: { input: { app: fileURLToPath(new URL('./index.html', import.meta.url)), demo: fileURLToPath(new URL('./demo.html', import.meta.url)) } } },
});
