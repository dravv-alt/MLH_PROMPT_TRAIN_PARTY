import { defineConfig } from 'vite';
import base from './vite.config.js';

export default defineConfig({
  ...base,
  plugins: base.plugins || [],
});
