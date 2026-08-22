import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  base: './',
  plugins: [
    vue(),
    vueDevTools(),
  ],
  server: {
    allowedHosts: true,
    proxy: {
      '/docs': {
        target: 'http://careequity-main-backend:8000',
        changeOrigin: true,
      },
      '/openapi.json': {
        target: 'http://careequity-main-backend:8000',
        changeOrigin: true,
      },
      '/ocr-docs': {
        target: 'http://careequity-ocr-backend:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/ocr-docs/, '/docs')
      },
      '/ocr-openapi.json': {
        target: 'http://careequity-ocr-backend:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/ocr-openapi.json/, '/openapi.json')
      }
    }
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  optimizeDeps: {
    include: ['vis-network/standalone']
  }
})
