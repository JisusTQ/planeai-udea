// ============================================================
//  Cliente HTTP: única capa que habla con la API del backend.
//  Centralizar las llamadas aquí mantiene los componentes limpios.
// ============================================================

// URL base de la API. Se puede sobrescribir con la variable de entorno
// VITE_API_URL (p. ej. en producción); por defecto apunta al backend local.
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/** Lista todos los cursos (opcionalmente filtrables más adelante). */
export async function listarCursos() {
  const res = await fetch(`${API_URL}/cursos`);
  if (!res.ok) throw new Error("No se pudieron cargar los cursos.");
  return res.json();
}

/** Obtiene los grupos (cupos, horario, profesor) de una materia por su código. */
export async function obtenerGrupos(codigo) {
  const res = await fetch(`${API_URL}/cursos/${codigo}/grupos`);
  if (!res.ok) throw new Error("No se pudieron cargar los grupos.");
  return res.json();
}

/** Envía un mensaje al asistente y devuelve su respuesta. */
export async function enviarMensaje(mensaje) {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mensaje }),
  });
  if (!res.ok) {
    // El backend devuelve {detail: "..."} en los errores (p. ej. 503 sin API key).
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Ocurrió un error al consultar al asistente.");
  }
  return res.json();
}
