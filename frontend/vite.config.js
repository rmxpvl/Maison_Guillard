import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// /api is forwarded to FastAPI so the browser only ever talks to one origin in dev.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:3000',
    },
  },
})
