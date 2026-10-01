import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// Every prefix the API owns. In development the browser talks only to this dev
// server, so they are proxied through to uvicorn — which also means cookies
// behave exactly as they do in production, because either way the browser sees
// a single origin and a same-site request.
const API_PREFIXES = [
  '/expenses',
  '/analytics',
  '/reports',
  '/register',
  '/login',
  '/logout',
  '/me',
  '/docs',
  '/openapi.json',
]

export default defineConfig({
  plugins: [react()],

  // Served under /app so the client's own routes cannot shadow the API's —
  // /expenses is an API path, and mounting the client at the root would take
  // it away from the server.
  base: '/app/',

  server: {
    proxy: Object.fromEntries(
      API_PREFIXES.map((prefix) => [prefix, { target: 'http://localhost:8000' }]),
    ),
  },

  build: {
    // Named to match the directory app/api.py mounts.
    outDir: 'dist',
    // Shipped alongside the source map so a production stack trace is readable.
    sourcemap: true,
  },

  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',
    // Components are tested through the DOM, not by asserting on stylesheets.
    css: false,
  },
})
