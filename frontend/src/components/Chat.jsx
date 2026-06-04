import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";

import { enviarMensaje, obtenerSugerencias } from "../api.js";
import {
  cargarActual,
  guardarActual,
  cargarHistorial,
  guardarHistorial,
} from "../historial.js";
import {
  IconSend,
  IconPlus,
  IconCopy,
  IconCheck,
  IconBolt,
  IconHistorial,
  IconTrash,
} from "./icons.jsx";

const SUGERENCIAS_INICIALES = [
  "Soy de primer semestre, ¿qué matriculo en la mañana?",
  "¿Qué grupos de Cálculo Integral tienen cupo?",
  "Ármame un horario de segundo semestre sin choques.",
  "¿Qué puedo ver si ya aprobé Cálculo Diferencial?",
  "Muéstrame materias con pocos cupos disponibles.",
  "¿Qué profesores dictan Matemáticas Discretas?",
];

const barajar = (arr) => [...arr].sort(() => Math.random() - 0.5);
const sugerirIniciales = () => barajar(SUGERENCIAS_INICIALES).slice(0, 4);

const SALUDO = {
  rol: "bot",
  texto:
    "Hola, soy **PlaneAI**. Consulto en vivo el pensum y los cupos de Ingeniería de Sistemas de la UdeA para ayudarte a planear tu semestre. ¿Por dónde empezamos?",
};

const NOMBRE_TOOL = {
  consultar_pensum: "Pensum",
  consultar_horarios_udea: "Cupos y horarios",
};

function etiquetaPaso(paso) {
  const nombre = NOMBRE_TOOL[paso.herramienta] || paso.herramienta;
  const arg = paso.args?.nivel || paso.args?.materia || "";
  const corto = arg.length > 30 ? `${arg.slice(0, 30)}…` : arg;
  return corto ? `${nombre}: ${corto}` : nombre;
}

function formatoFecha(ts) {
  const d = new Date(ts);
  const hora = d.toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" });
  if (d.toDateString() === new Date().toDateString()) return `Hoy ${hora}`;
  return `${d.toLocaleDateString("es", { day: "2-digit", month: "short" })} ${hora}`;
}

function RespuestaBot({ texto, pasos }) {
  const [copiado, setCopiado] = useState(false);

  function copiar() {
    navigator.clipboard?.writeText(texto).then(() => {
      setCopiado(true);
      setTimeout(() => setCopiado(false), 1500);
    });
  }

  return (
    <div className="bubble">
      <ReactMarkdown>{texto}</ReactMarkdown>
      {pasos?.length > 0 && (
        <div className="pasos">
          <IconBolt width={13} height={13} />
          {pasos.map((p, i) => (
            <span key={i} className="paso">
              {etiquetaPaso(p)}
            </span>
          ))}
        </div>
      )}
      <button className="copiar" onClick={copiar} aria-label="Copiar respuesta">
        {copiado ? <IconCheck width={14} height={14} /> : <IconCopy width={14} height={14} />}
      </button>
    </div>
  );
}

export default function Chat() {
  const [mensajes, setMensajes] = useState(() => cargarActual() ?? [SALUDO]);
  const [historial, setHistorial] = useState(() => cargarHistorial());
  const [mostrarHistorial, setMostrarHistorial] = useState(false);
  const [entrada, setEntrada] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [sugerencias, setSugerencias] = useState(sugerirIniciales);
  const finRef = useRef(null);
  const areaRef = useRef(null);

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajes, cargando]);

  useEffect(() => {
    guardarActual(mensajes);
  }, [mensajes]);

  function persistirHistorial(lista) {
    setHistorial(lista);
    guardarHistorial(lista);
  }

  // Archiva la conversación actual en el historial si tiene mensajes del usuario.
  function archivar(lista) {
    const primera = mensajes.find((m) => m.rol === "user");
    if (!primera) return lista;
    const conv = {
      id: Date.now(),
      titulo: primera.texto.slice(0, 60),
      fecha: Date.now(),
      mensajes,
    };
    return [conv, ...lista];
  }

  async function pedirRespuesta(conversacion) {
    setCargando(true);
    setError(null);
    setSugerencias([]);
    const previos = conversacion.slice(0, -1);
    const msg = conversacion[conversacion.length - 1].texto;
    try {
      const data = await enviarMensaje(msg, previos);
      const nueva = [...conversacion, { rol: "bot", texto: data.respuesta, pasos: data.pasos }];
      setMensajes(nueva);
      obtenerSugerencias(nueva)
        .then((d) => d.sugerencias?.length && setSugerencias(d.sugerencias))
        .catch(() => {});
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }

  function enviar(texto) {
    const msg = (texto ?? entrada).trim();
    if (!msg || cargando) return;
    setEntrada("");
    if (areaRef.current) areaRef.current.style.height = "auto";
    const conversacion = [...mensajes, { rol: "user", texto: msg }];
    setMensajes(conversacion);
    pedirRespuesta(conversacion);
  }

  function nuevaConversacion() {
    if (cargando) return;
    persistirHistorial(archivar(historial));
    setMensajes([SALUDO]);
    setEntrada("");
    setError(null);
    setSugerencias(sugerirIniciales());
    setMostrarHistorial(false);
  }

  function cargarConversacion(conv) {
    persistirHistorial(archivar(historial).filter((c) => c.id !== conv.id));
    setMensajes(conv.mensajes);
    setError(null);
    setSugerencias(sugerirIniciales());
    setMostrarHistorial(false);
  }

  function borrarConversacion(id, e) {
    e.stopPropagation();
    persistirHistorial(historial.filter((c) => c.id !== id));
  }

  return (
    <div className="view">
      <div className="view-head con-accion">
        <div>
          <h2>Asistente</h2>
          <p>Pregunta por materias, cupos y horarios en lenguaje natural.</p>
        </div>

        <div className="head-acciones">
          <div className="historial-wrap">
            <button className="btn-ghost" onClick={() => setMostrarHistorial((v) => !v)}>
              <IconHistorial width={16} height={16} /> Historial
              {historial.length > 0 ? ` (${historial.length})` : ""}
            </button>
            {mostrarHistorial && (
              <>
                <div className="overlay-historial" onClick={() => setMostrarHistorial(false)} />
                <div className="historial-panel">
                  {historial.length === 0 ? (
                    <p className="historial-vacio">Aún no tienes conversaciones guardadas.</p>
                  ) : (
                    historial.map((c) => (
                      <div key={c.id} className="historial-item">
                        <button
                          className="historial-cargar"
                          onClick={() => cargarConversacion(c)}
                        >
                          <span className="historial-titulo">{c.titulo}</span>
                          <span className="historial-fecha">{formatoFecha(c.fecha)}</span>
                        </button>
                        <button
                          className="historial-borrar"
                          onClick={(e) => borrarConversacion(c.id, e)}
                          aria-label="Borrar conversación"
                        >
                          <IconTrash width={15} height={15} />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </>
            )}
          </div>

          {mensajes.length > 1 && (
            <button className="btn-ghost" onClick={nuevaConversacion} disabled={cargando}>
              <IconPlus width={16} height={16} /> Nueva
            </button>
          )}
        </div>
      </div>

      <div className="chat-scroll">
        <div className="thread">
          {mensajes.map((m, i) => (
            <div key={i} className={`row ${m.rol}`}>
              <div className={`avatar ${m.rol === "bot" ? "bot" : "me"}`}>
                {m.rol === "bot" ? "P" : "Tú"}
              </div>
              {m.rol === "bot" ? (
                <RespuestaBot texto={m.texto} pasos={m.pasos} />
              ) : (
                <div className="bubble">{m.texto}</div>
              )}
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

          {error && (
            <div className="banner-error">
              <span>{error}</span>
              <button onClick={() => pedirRespuesta(mensajes)} disabled={cargando}>
                Reintentar
              </button>
            </div>
          )}
          <div ref={finRef} />
        </div>
      </div>

      <div className="composer">
        {!cargando && sugerencias.length > 0 && (
          <div className="chips">
            {sugerencias.map((s) => (
              <button key={s} className="chip" onClick={() => enviar(s)}>
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
