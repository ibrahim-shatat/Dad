import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: true,
    port: 5173,
    // Docker Desktop on Windows doesn't propagate inotify events into the container for
    // bind-mounted files, so chokidar's default watcher never fires — poll instead.
    watch: {
      usePolling: true,
      interval: 300,
    },
  },
})
