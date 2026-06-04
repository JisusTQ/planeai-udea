"""
Entorno de ejecución de Alembic para PlaneAI UdeA.

Este script conecta Alembic con:
  · La configuración de la app: lee DATABASE_URL del .env (sin exponerla en
    alembic.ini, que sí se versiona en Git).
  · Los modelos SQLAlchemy (Base.metadata): así `--autogenerate` detecta
    automáticamente las tablas y sus cambios al generar cada migración.
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Importamos la configuración y, MUY IMPORTANTE, todos los modelos, para que
# queden registrados en Base.metadata antes de generar las migraciones.
from app.config import get_settings
from app.database import Base
import app.models  # noqa: F401  (registra Curso, Grupo, Profesor y curso_prerrequisito)

# Objeto de configuración de Alembic (corresponde a alembic.ini).
config = context.config

# Inyectamos la URL de la base de datos desde el .env (no se guarda en el .ini).
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Configuración del sistema de logging a partir del archivo .ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadatos de los modelos: es lo que habilita la detección automática de cambios.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Modo 'offline': genera el SQL de la migración sin conectarse a la BD."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Modo 'online': se conecta a la BD (Neon) y aplica las migraciones."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
