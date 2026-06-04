import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Configuración de Vite para el frontend de PlaneAI UdeA.
// El backend (FastAPI) ya habilita CORS para http://localhost:5173,
// así que el frontend puede llamar directamente a la API en el puerto 8000.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
});
