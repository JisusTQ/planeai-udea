import { useState, useRef, useEffect } from "react";

import { enviarMensaje } from "../api.js";

// Preguntas de ejemplo para que el estudiante empiece con un clic.
const SUGERENCIAS = [
  "Soy de primer semestre, ¿qué materias puedo matricular en la mañana?",
  "¿Qué grupos de Cálculo Integral tienen cupo?",
  "Ármame un horario sin choques para segundo semestre.",
];

export default function Chat() {
  const [mensajes, setMensajes] = useState([
    {
      rol: "asistente",
      texto:
        "¡Hola! Soy PlaneAI 🤖. Pregúntame por cursos, cupos u horarios y te ayudo a planear tu semestre.",
    },
  ]);
  const [entrada, setEntrada] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const finRef = useRef(null);

  // Auto-scroll hacia el último mensaje cada vez que cambia la conversación.
  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajes, cargando]);

  async function enviar(texto) {
    const msg = (texto ?? entrada).trim();
    if (!msg || cargando) return;

    setError(null);
    setEntrada("");
    setMensajes((prev) => [...prev, { rol: "usuario", texto: msg }]);
    setCargando(true);

    try {
      const data = await enviarMensaje(msg);
      setMensajes((prev) => [...prev, { rol: "asistente", texto: data.respuesta }]);
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="chat">
      <div className="mensajes">
        {mensajes.map((m, i) => (
          <div key={i} className={`burbuja ${m.rol}`}>
            {m.texto}
          </div>
        ))}
        {cargando && (
          <div className="burbuja asistente cargando">PlaneAI está pensando…</div>
        )}
        {error && <div className="burbuja error">⚠️ {error}</div>}
        <div ref={finRef} />
      </div>

      <div className="sugerencias">
        {SUGERENCIAS.map((s, i) => (
          <button key={i} onClick={() => enviar(s)} disabled={cargando}>
            {s}
          </button>
        ))}
      </div>

      <form
        className="entrada"
        onSubmit={(e) => {
          e.preventDefault();
          enviar();
        }}
      >
        <input
          type="text"
          value={entrada}
          onChange={(e) => setEntrada(e.target.value)}
          placeholder="Escribe tu pregunta…"
          disabled={cargando}
        />
        <button type="submit" disabled={cargando || !entrada.trim()}>
          Enviar
        </button>
      </form>
    </div>
  );
}
