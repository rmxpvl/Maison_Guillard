import { appendFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// robots.txt tells search engines where the sitemap is. The sitemap is built by the API (it lists the
// products and posts of the database), so its address depends on VITE_API_URL, known only at build time.
function sitemapDansRobots(apiUrl) {
  let dossier = 'dist'
  return {
    name: 'sitemap-dans-robots',
    apply: 'build',
    configResolved(config) {
      dossier = resolve(config.root, config.build.outDir)
    },
    closeBundle() {
      const robots = resolve(dossier, 'robots.txt')
      if (!apiUrl || !existsSync(robots)) return
      appendFileSync(robots, `\nSitemap: ${apiUrl.replace(/\/$/, '')}/sitemap.xml\n`)
    },
  }
}

export default defineConfig(({ mode }) => ({
  plugins: [react(), sitemapDansRobots(loadEnv(mode, process.cwd()).VITE_API_URL)],
  server: {
    // /api is forwarded to FastAPI so the browser only ever talks to one origin in dev.
    proxy: {
      '/api': 'http://localhost:3000',
    },
  },
}))
