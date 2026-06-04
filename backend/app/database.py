"""
Configuración de la conexión a PostgreSQL (Neon) con SQLAlchemy.

Aquí definimos las tres piezas clave del acceso a datos:
- `engine`      : motor que administra el pool de conexiones a PostgreSQL.
- `SessionLocal`: fábrica de sesiones para hablar con la BD en cada petición.
- `Base`        : clase base de la que heredan TODOS los modelos ORM.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

# El motor administra el pool de conexiones a PostgreSQL.
# - pool_pre_ping=True: verifica que la conexión siga viva antes de usarla.
#   Es importante con bases en la nube (Neon) que cierran conexiones inactivas.
# - echo=False: poner en True para ver en consola el SQL generado (depuración).
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

# Cada instancia de SessionLocal representa una sesión/transacción independiente.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base declarativa: Curso, Grupo y Profesor heredarán de ella.
Base = declarative_base()


def get_db():
    """
    Dependencia de FastAPI que entrega una sesión de BD por petición y
    garantiza cerrarla al terminar (patrón de inyección de dependencias).

    Se usará así en los routers:
        def endpoint(db: Session = Depends(get_db)): ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
