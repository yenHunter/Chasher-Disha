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
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Cross-Origin-Embedder-Policy': 'require-corp',
        },
    },
    build: {
        outDir: 'dist',
        emptyOutDir: true,
        sourcemap: false,
        rollupOptions: {
            output: {
                // Split onnxruntime-web into a separate chunk (large, lazy-loaded)
                manualChunks(id) {
                    if (id.includes('onnxruntime-web'))
                        return 'onnx-runtime';
                    if (id.includes('node_modules'))
                        return 'vendor';
                },
            },
        },
    },
    // Treat .onnx files as static assets
    assetsInclude: ['**/*.onnx'],
    optimizeDeps: {
        // onnxruntime-web must not be pre-bundled — it ships its own WASM
        exclude: ['onnxruntime-web'],
    },
});
