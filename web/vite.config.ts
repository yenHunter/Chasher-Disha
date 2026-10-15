import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': '/src' },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
    // M7: OFFLINE-3 — ONNX WASM requires SharedArrayBuffer; needs COOP/COEP headers
    headers: {
      'Cross-Origin-Opener-Policy':   'same-origin',
      'Cross-Origin-Embedder-Policy': 'require-corp',
    },
  },
  build: {
    outDir:     'dist',
    emptyOutDir: true,
    sourcemap:   false,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('onnxruntime-web')) return 'onnx-runtime';
          if (id.includes('node_modules'))   return 'vendor';
        },
      },
    },
  },
  assetsInclude: ['**/*.onnx'],
  optimizeDeps: {
    exclude: ['onnxruntime-web'],
  },
  // M8: TEST-2 — Vitest configuration
  test: {
    globals:     true,
    environment: 'jsdom',
    setupFiles:  ['./src/__tests__/vitest.setup.ts'],
    include:     ['src/__tests__/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include:  ['src/**/*.{ts,tsx}'],
      exclude:  ['src/__tests__/**', 'src/main.tsx'],
    },
  },
});
