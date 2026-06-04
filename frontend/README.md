# Frontend — PlaneAI UdeA

Interfaz web del asistente, construida con **React + Vite**.

Consume la API del backend (FastAPI) para dos vistas: el **chat con el agente** y
la **vista de cupos en vivo**. No contiene lógica de negocio: solo presenta lo que
devuelve el backend.

## Estructura

```
frontend/
├── index.html
├── package.json
├── vite.config.js
└── src/
    ├── main.jsx              # Punto de montaje de React
    ├── App.jsx              # Componente raíz (pestañas: chat + cupos)
    ├── index.css           # Estilos
    ├── api.js              # Cliente HTTP: única capa que habla con la API
    └── components/
        ├── Chat.jsx        # Chat conversacional con el agente (/chat)
        └── VistaCupos.jsx  # Cursos + cupos/horarios en vivo
```

## Vistas principales

1. **Chat conversacional** (`Chat.jsx`) — el estudiante escribe y PlaneAI responde.
   El backend es un **agente Gemini** que consulta en vivo el pensum y los cupos de
   la UdeA; el frontend solo envía el mensaje a `POST /chat` y muestra la respuesta.
2. **Vista de cupos** (`VistaCupos.jsx`) — lista los cursos del catálogo
   (`GET /cursos`) y, al elegir uno, muestra sus grupos, cupos y horarios
   **en vivo** (`GET /cursos/{id}/grupos`).

## Cliente API (`src/api.js`)

| Función | Endpoint | Uso |
|---|---|---|
| `listarCursos()` | `GET /cursos` | Catálogo de cursos |
| `obtenerGrupos(id)` | `GET /cursos/{id}/grupos` | Grupos/cupos/horarios en vivo |
| `enviarMensaje(texto)` | `POST /chat` | Pregunta al agente |

La URL base de la API se toma de la variable de entorno **`VITE_API_URL`** y, si no
está definida, usa `http://localhost:8000` por defecto.

## Cómo ejecutar

```bash
npm install
npm run dev
#   App: http://localhost:5173
```

Requiere el **backend en ejecución** (ver el README principal). Si el backend no
está en `http://localhost:8000`, crea un archivo `.env` en esta carpeta:

```
VITE_API_URL=http://localhost:8001
```

y asegúrate de que el origen del frontend (p. ej. `http://localhost:5173`) esté
incluido en `CORS_ORIGINS` del backend.

> **Nota:** Vite elige otro puerto automáticamente si el 5173 está ocupado; en ese
> caso, agrega ese nuevo origen a `CORS_ORIGINS` del backend.
