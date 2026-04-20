import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/upload": "http://localhost:8080",
      "/status": "http://localhost:8080",
      "/download": "http://localhost:8080",
      "/stats": "http://localhost:8080",
      "/health": "http://localhost:8080",
    },
  },
});
