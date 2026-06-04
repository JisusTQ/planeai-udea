import { useState, useEffect, useMemo } from "react";

import { listarCursos, obtenerGrupos } from "../api.js";
import { IconSearch, IconUser, IconClock, IconPin } from "./icons.jsx";

const etiquetaNivel = (n) => (n === 99 ? "Electivas" : `Sem ${n}`);

function estadoCupo(disponibles) {
  if (disponibles <= 0) return "lleno";
  if (disponibles <= 5) return "bajo";
  return "ok";
}

export default function VistaCupos() {
  const [cursos, setCursos] = useState([]);
  const [q, setQ] = useState("");
  const [nivel, setNivel] = useState(null);
  const [sel, setSel] = useState(null);
  const [grupos, setGrupos] = useState([]);
  const [cargandoCursos, setCargandoCursos] = useState(true);
  const [cargandoGrupos, setCargandoGrupos] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    listarCursos()
      .then(setCursos)
      .catch((e) => setError(e.message))
      .finally(() => setCargandoCursos(false));
  }, []);

  const niveles = useMemo(
    () => [...new Set(cursos.map((c) => c.nivel))].sort((a, b) => a - b),
    [cursos]
  );

  const filtrados = useMemo(() => {
    const t = q.trim().toLowerCase();
    return cursos.filter(
      (c) =>
        (nivel == null || c.nivel === nivel) &&
        (!t || c.nombre.toLowerCase().includes(t) || String(c.codigo).includes(t))
    );
  }, [cursos, q, nivel]);

  async function abrir(curso) {
    setSel(curso);
    setCargandoGrupos(true);
    setError(null);
    try {
      setGrupos(await obtenerGrupos(curso.codigo));
    } catch (e) {
      setError(e.message);
      setGrupos([]);
    } finally {
      setCargandoGrupos(false);
    }
  }

  return (
    <div className="view">
      <div className="view-head cupos-head">
        <div>
          <h2>Cupos y horarios</h2>
          <p>Oferta vigente consultada en vivo desde el portal de la UdeA.</p>
        </div>

        <div className="buscador">
          <IconSearch width={18} height={18} />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Buscar materia o código…"
          />
        </div>

        {niveles.length > 0 && (
          <div className="niveles">
            <button
              className={`nivel-chip ${nivel == null ? "on" : ""}`}
              onClick={() => setNivel(null)}
            >
              Todas
            </button>
            {niveles.map((n) => (
              <button
                key={n}
                className={`nivel-chip ${nivel === n ? "on" : ""}`}
                onClick={() => setNivel(n)}
              >
                {etiquetaNivel(n)}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="cupos-body">
        <div className="lista">
          {cargandoCursos &&
            Array.from({ length: 7 }).map((_, i) => (
              <div
                key={i}
                className="sk-line skeleton"
                style={{ width: `${65 + (i % 3) * 12}%`, height: 34 }}
              />
            ))}

          {!cargandoCursos && filtrados.length === 0 && (
            <p className="placeholder">Sin resultados.</p>
          )}

          {filtrados.map((c) => (
            <button
              key={c.codigo}
              className={`curso-item ${sel?.codigo === c.codigo ? "on" : ""}`}
              onClick={() => abrir(c)}
            >
              <b>{c.nombre}</b>
              <small>
                {c.codigo} · {etiquetaNivel(c.nivel)} · {c.creditos} créditos
              </small>
            </button>
          ))}
        </div>

        <div className="detalle">
          {!sel && (
            <div className="placeholder">
              <p>
                Elige una materia de la izquierda para ver sus grupos, cupos y
                horarios en vivo.
              </p>
            </div>
          )}

          {sel && (
            <>
              <div className="detalle-titulo">{sel.nombre}</div>
              <div className="detalle-meta">
                Código {sel.codigo} · {etiquetaNivel(sel.nivel)} · {sel.creditos} créditos
              </div>

              {error && <div className="banner-error">{error}</div>}

              {cargandoGrupos && (
                <div className="grupos-grid">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="grupo">
                      <div className="sk-line skeleton" style={{ width: "45%" }} />
                      <div className="sk-line skeleton" />
                      <div className="sk-line skeleton" style={{ width: "70%" }} />
                    </div>
                  ))}
                </div>
              )}

              {!cargandoGrupos && !error && grupos.length === 0 && (
                <p className="placeholder">
                  Esta materia no aparece en la oferta vigente de este semestre.
                </p>
              )}

              {!cargandoGrupos && grupos.length > 0 && (
                <div className="grupos-grid">
                  {grupos.map((g) => {
                    const est = estadoCupo(g.cupos_disponibles);
                    const pct = g.cupos_totales
                      ? Math.round((g.cupos_disponibles / g.cupos_totales) * 100)
                      : 0;
                    return (
                      <div key={g.id} className="grupo">
                        <div className="grupo-top">
                          <span className="grupo-num">Grupo {g.numero}</span>
                          <span className={`cupo-tag ${est}`}>
                            {g.cupos_disponibles}/{g.cupos_totales}
                          </span>
                        </div>
                        <div className="barra">
                          <i className={est} style={{ width: `${pct}%` }} />
                        </div>
                        <div className="dato">
                          <IconUser width={16} height={16} />
                          {g.profesor?.nombre ?? "Sin asignar"}
                        </div>
                        <div className="dato">
                          <IconPin width={16} height={16} />
                          {g.aula ?? "Por definir"}
                        </div>
                        {g.horario.length > 0 && (
                          <div className="sesiones">
                            {g.horario.map((s, i) => (
                              <span key={i} className="sesion">
                                <IconClock width={13} height={13} /> {s.dia.slice(0, 3)}{" "}
                                {s.hora_inicio}–{s.hora_fin}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
