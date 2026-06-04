const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function pedir(ruta, opciones) {
  const res = await fetch(`${API_URL}${ruta}`, opciones);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "No se pudo completar la solicitud.");
  }
  return res.json();
}

const enviarJson = (cuerpo) => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(cuerpo),
});

const soloMensajes = (historial) => historial.map((m) => ({ rol: m.rol, texto: m.texto }));

export const listarCursos = (nivel) =>
  pedir(`/cursos${nivel ? `?nivel=${nivel}` : ""}`);

export const obtenerGrupos = (codigo) => pedir(`/cursos/${codigo}/grupos`);

export const enviarMensaje = (mensaje, historial = []) =>
  pedir("/chat", enviarJson({ mensaje, historial: soloMensajes(historial) }));

export const obtenerSugerencias = (historial = []) =>
  pedir("/chat/sugerencias", enviarJson({ historial: soloMensajes(historial) }));
