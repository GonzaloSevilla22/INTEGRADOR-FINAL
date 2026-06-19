import { defineConfig } from "vite";

export default defineConfig({
  server: {
    port: 5500,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => {
          // Llamadas con doble /api (pagos/estadisticas desde frontend):
          // /api/api/v1/pagos/... → quitar primer /api → /api/v1/pagos/...
          if (path.startsWith("/api/api/")) return path.slice(4);
          // Llamadas directas externas (ej: webhook MP): /api/v1/... → pasar sin cambio
          if (path.startsWith("/api/v1/")) return path;
          // Llamadas estándar: /api/productos/... → quitar /api → /productos/...
          return path.replace(/^\/api/, "");
        },
        ws: true,
      },
    },
  },
});
