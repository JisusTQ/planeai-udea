import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";

import { enviarMensaje } from "../api.js";
import { IconSend } from "./icons.jsx";

const SUGERENCIAS = [
  "Soy de primer semestre, ¿qué materias matriculo en la mañana?",
  "¿Qué grupos de Cálculo Integral tienen cupo?",
  "Ármame un horario de segundo semestre sin choques.",
];

const SALUDO = {
  rol: "bot",
  texto:
    "Hola, soy **PlaneAI**. Consulto en vivo el pensum y los cupos de Ingeniería de Sistemas de la UdeA para ayudarte a planear tu semestre. ¿Por dónde empezamos?",
};

export default function Chat() {
  const [mensajes, setMensajes] = useState([SALUDO]);
  const [entrada, setEntrada] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const finRef = useRef(null);
  const areaRef = useRef(null);

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajes, cargando]);

  async function enviar(texto) {
    const msg = (texto ?? entrada).trim();
    if (!msg || cargando) return;

    setError(null);
    setEntrada("");
    if (areaRef.current) areaRef.current.style.height = "auto";
    setMensajes((p) => [...p, { rol: "user", texto: msg }]);
    setCargando(true);

    try {
      const data = await enviarMensaje(msg);
      setMensajes((p) => [...p, { rol: "bot", texto: data.respuesta }]);
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="view">
      <div className="view-head">
        <h2>Asistente</h2>
        <p>Pregunta por materias, cupos y horarios en lenguaje natural.</p>
      </div>

      <div className="chat-scroll">
        <div className="thread">
          {mensajes.map((m, i) => (
            <div key={i} className={`row ${m.rol}`}>
              <div className={`avatar ${m.rol === "bot" ? "bot" : "me"}`}>
                {m.rol === "bot" ? "P" : "Tú"}
              </div>
              <div className="bubble">
                {m.rol === "bot" ? <ReactMarkdown>{m.texto}</ReactMarkdown> : m.texto}
              </div>
            </div>
          ))}

          {cargando && (
            <div className="row bot">
              <div className="avatar bot">P</div>
              <div className="bubble">
                <div className="typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          )}

          {error && <div className="banner-error">{error}</div>}
          <div ref={finRef} />
        </div>
      </div>

      <div className="composer">
        {mensajes.length === 1 && (
          <div className="chips">
            {SUGERENCIAS.map((s) => (
              <button key={s} className="chip" onClick={() => enviar(s)} disabled={cargando}>
                {s}
              </button>
            ))}
          </div>
        )}

        <form
          className="input-line"
          onSubmit={(e) => {
            e.preventDefault();
            enviar();
          }}
        >
          <textarea
            ref={areaRef}
            rows={1}
            value={entrada}
            placeholder="Escribe tu pregunta…"
            disabled={cargando}
            onChange={(e) => {
              setEntrada(e.target.value);
              e.target.style.height = "auto";
              e.target.style.height = `${e.target.scrollHeight}px`;
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                enviar();
              }
            }}
          />
          <button
            className="send"
            type="submit"
            disabled={cargando || !entrada.trim()}
            aria-label="Enviar"
          >
            <IconSend width={19} height={19} />
          </button>
        </form>
      </div>
    </div>
  );
}
