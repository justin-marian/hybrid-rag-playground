import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiTarget = env.VITE_API_URL || "http://localhost:8000";

  return {
    plugins: [react()],
    server: {
      port: 5173,
      strictPort: false,
      // Proxy /api/* during development so the browser never needs to know
      // about the backend URL (avoids CORS complications during local dev).
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true
        },
      },
    },
    preview: {
      port: 4173
    },
    build: {
      outDir: "dist",
      sourcemap: true
    },
  };
});
