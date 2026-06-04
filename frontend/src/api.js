const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function pedir(ruta, opciones) {
  const res = await fetch(`${API_URL}${ruta}`, opciones);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "No se pudo completar la solicitud.");
  }
  return res.json();
}

export const listarCursos = (nivel) =>
  pedir(`/cursos${nivel ? `?nivel=${nivel}` : ""}`);

export const obtenerGrupos = (codigo) => pedir(`/cursos/${codigo}/grupos`);

export const enviarMensaje = (mensaje) =>
  pedir("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mensaje }),
  });
