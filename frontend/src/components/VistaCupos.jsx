import { useState, useEffect } from "react";

import { listarCursos, obtenerGrupos } from "../api.js";

export default function VistaCupos() {
  const [cursos, setCursos] = useState([]);
  const [seleccionado, setSeleccionado] = useState(null);
  const [grupos, setGrupos] = useState([]);
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(false);

  // Al montar el componente, cargamos la lista de cursos.
  useEffect(() => {
    listarCursos()
      .then(setCursos)
      .catch((e) => setError(e.message));
  }, []);

  async function verGrupos(curso) {
    setSeleccionado(curso);
    setCargando(true);
    setError(null);
    try {
      setGrupos(await obtenerGrupos(curso.id));
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }

  // Color del indicador según la disponibilidad de cupos.
  function colorCupos(disponibles) {
    if (disponibles === 0) return "sin-cupo";
    if (disponibles <= 5) return "pocos-cupos";
    return "con-cupo";
  }

  return (
    <div className="cupos">
      <aside className="lista-cursos">
        <h3>Cursos</h3>
        {error && !seleccionado && <p className="error-texto">⚠️ {error}</p>}
        <ul>
          {cursos.map((c) => (
            <li
              key={c.id}
              className={seleccionado?.id === c.id ? "activo" : ""}
              onClick={() => verGrupos(c)}
            >
              <strong>{c.nombre}</strong>
              <span>
                {c.codigo} · sem {c.semestre ?? "-"} · {c.creditos} cr
              </span>
            </li>
          ))}
        </ul>
      </aside>

      <section className="detalle-grupos">
        {!seleccionado && (
          <p className="vacio">Selecciona un curso para ver sus grupos y cupos.</p>
        )}

        {seleccionado && (
          <>
            <h3>
              {seleccionado.nombre} <small>({seleccionado.codigo})</small>
            </h3>
            {cargando && <p>Cargando grupos…</p>}
            {error && <p className="error-texto">⚠️ {error}</p>}
            {!cargando && grupos.length === 0 && (
              <p className="vacio">Este curso no tiene grupos registrados.</p>
            )}

            <div className="grid-grupos">
              {grupos.map((g) => (
                <div key={g.id} className="tarjeta-grupo">
                  <div className="grupo-encabezado">
                    <span className="grupo-numero">Grupo {g.numero}</span>
                    <span className={`badge ${colorCupos(g.cupos_disponibles)}`}>
                      {g.cupos_disponibles}/{g.cupos_totales} cupos
                    </span>
                  </div>
                  <p className="grupo-prof">👤 {g.profesor?.nombre ?? "Sin asignar"}</p>
                  <p className="grupo-aula">📍 {g.aula ?? "Aula por definir"}</p>
                  <ul className="grupo-horario">
                    {g.horario.map((s, i) => (
                      <li key={i}>
                        🕒 {s.dia} {s.hora_inicio}–{s.hora_fin}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
