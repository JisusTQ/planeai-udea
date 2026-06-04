-- ============================================================
--  PlaneAI UdeA · Esquema de la base de datos (PostgreSQL)
-- ------------------------------------------------------------
--  Este archivo es el DDL de REFERENCIA del modelo de datos.
--
--  En el flujo real del proyecto, las tablas se crean y versionan
--  con Alembic (migraciones), a partir de los modelos SQLAlchemy
--  ubicados en backend/app/models/. Este script refleja exactamente
--  esos modelos y sirve para:
--    1. Revisar el diseño de forma clara (legible por humanos).
--    2. Levantar la BD manualmente si se desea, sin Alembic.
--
--  Relaciones:
--    cursos (1) ──< grupos >── (1) profesores
--        Un curso tiene muchos grupos; un profesor dicta muchos grupos.
--    cursos (N) ──< curso_prerrequisito >── (N) cursos
--        Un curso puede requerir varios cursos como prerrequisito
--        (relación muchos-a-muchos de cursos consigo mismo).
-- ============================================================

-- ------------------------------------------------------------
-- Tabla: cursos
-- Catálogo de asignaturas del pensum (la materia "en abstracto").
-- ------------------------------------------------------------
CREATE TABLE cursos (
    id          SERIAL       PRIMARY KEY,
    codigo      VARCHAR(20)  NOT NULL UNIQUE,   -- código institucional UdeA
    nombre      VARCHAR(200) NOT NULL,
    creditos    INTEGER      NOT NULL,
    semestre    INTEGER,                        -- semestre sugerido en el plan (1-10)
    programa    VARCHAR(150) NOT NULL,
    descripcion TEXT
);

CREATE INDEX ix_cursos_codigo   ON cursos (codigo);
CREATE INDEX ix_cursos_programa ON cursos (programa);

-- ------------------------------------------------------------
-- Tabla: profesores
-- Docentes. Se normaliza en su propia tabla para no repetir el
-- nombre del profesor en cada grupo y poder filtrar/recomendar por él.
-- ------------------------------------------------------------
CREATE TABLE profesores (
    id           SERIAL       PRIMARY KEY,
    nombre       VARCHAR(150) NOT NULL,
    email        VARCHAR(150),
    departamento VARCHAR(150)
);

CREATE INDEX ix_profesores_nombre ON profesores (nombre);

-- ------------------------------------------------------------
-- Tabla: grupos
-- Oferta CONCRETA de un curso en un semestre académico.
-- Es la entidad central: conecta curso + profesor y guarda
-- cupos, horario (JSONB) y aula.
-- ------------------------------------------------------------
CREATE TABLE grupos (
    id                 SERIAL      PRIMARY KEY,
    numero             VARCHAR(10) NOT NULL,                 -- número de grupo (1, 2, ...)
    semestre_academico VARCHAR(10) NOT NULL,                 -- p. ej. "2025-1"
    cupos_totales      INTEGER     NOT NULL DEFAULT 0,
    cupos_disponibles  INTEGER     NOT NULL DEFAULT 0,
    horario            JSONB       DEFAULT '[]'::jsonb,      -- lista de sesiones (día/hora)
    aula               VARCHAR(50),

    -- Llaves foráneas
    curso_id    INTEGER NOT NULL REFERENCES cursos(id)     ON DELETE CASCADE,
    profesor_id INTEGER          REFERENCES profesores(id) ON DELETE SET NULL
);

CREATE INDEX ix_grupos_curso_id           ON grupos (curso_id);
CREATE INDEX ix_grupos_profesor_id        ON grupos (profesor_id);
CREATE INDEX ix_grupos_semestre_academico ON grupos (semestre_academico);

-- ------------------------------------------------------------
-- Tabla de asociación: curso_prerrequisito
-- Relación muchos-a-muchos de Curso consigo mismo: define qué
-- cursos son prerrequisito de cuáles.
--   Cada fila: "el curso `curso_id` requiere haber aprobado `prerrequisito_id`".
-- La llave primaria compuesta evita duplicar el mismo par.
-- ------------------------------------------------------------
CREATE TABLE curso_prerrequisito (
    curso_id         INTEGER NOT NULL REFERENCES cursos(id) ON DELETE CASCADE,
    prerrequisito_id INTEGER NOT NULL REFERENCES cursos(id) ON DELETE CASCADE,
    PRIMARY KEY (curso_id, prerrequisito_id)
);

-- ============================================================
--  Notas de diseño:
--
--  · ON DELETE CASCADE en grupos.curso_id:
--      si se elimina un curso, se eliminan sus grupos (no tiene
--      sentido un grupo sin curso). Coincide con cascade="all,
--      delete-orphan" del modelo SQLAlchemy.
--
--  · ON DELETE SET NULL en grupos.profesor_id:
--      si se elimina un profesor, sus grupos quedan "sin profesor
--      asignado" en lugar de borrarse.
--
--  · horario como JSONB:
--      ejemplo de contenido de una fila ->
--      [{"dia":"lunes","hora_inicio":"06:00","hora_fin":"08:00"},
--       {"dia":"miercoles","hora_inicio":"06:00","hora_fin":"08:00"}]
--      Permite varias sesiones por grupo y detectar choques de
--      horario al armar el plan del estudiante.
--
--  · curso_prerrequisito (auto-referencial N:M):
--      permite que el asistente avise, por ejemplo, que no se puede
--      matricular "Cálculo Integral" sin haber aprobado "Cálculo
--      Diferencial". Ambas FK apuntan a cursos(id).
-- ============================================================
