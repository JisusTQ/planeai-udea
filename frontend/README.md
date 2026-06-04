# Frontend — PlaneAI UdeA

Interfaz web del asistente, construida con **React + Vite**.

> ⚙️ Esta carpeta se inicializará con el andamiaje de Vite en la fase de frontend
> del proyecto (`npm create vite@latest`). Por ahora es un marcador de posición
> dentro de la estructura general.

## Estructura prevista

```
frontend/
├── src/
│   ├── components/      # Componentes de UI (ChatBox, MensajeBurbuja, TablaCupos...)
│   ├── services/        # Cliente HTTP que consume la API (api.js)
│   ├── App.jsx          # Componente raíz (chat + vista de cupos)
│   └── main.jsx         # Punto de montaje de React
├── index.html
├── package.json
└── vite.config.js
```

## Vistas principales

1. **Chat conversacional** — el estudiante escribe y PlaneAI (Gemini) responde
   con recomendaciones y horarios, usando los cursos reales de la BD como contexto.
2. **Vista de cupos** — tabla con los cupos disponibles por grupo de cada curso.
