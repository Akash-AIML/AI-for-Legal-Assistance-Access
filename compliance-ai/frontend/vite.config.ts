import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (
            id.includes("node_modules/react/") ||
            id.includes("node_modules/react-dom/") ||
            id.includes("node_modules/react-router") ||
            id.includes("node_modules/framer-motion")
          ) {
            return "vendor-react"
          }
          if (id.includes("node_modules/@radix-ui")) {
            return "vendor-ui"
          }
          if (id.includes("node_modules/lucide-react")) {
            return "vendor-icons"
          }
          if (id.includes("node_modules/jspdf")) {
            return "vendor-pdf"
          }
          if (id.includes("node_modules/marked")) {
            return "vendor-markdown"
          }
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
})