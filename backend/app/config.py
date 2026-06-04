"""
Configuración central de la aplicación.

Usamos `pydantic-settings` para leer las variables de entorno desde el
archivo .env de forma TIPADA y VALIDADA. Esto evita usar os.environ de forma
dispersa y centraliza toda la configuración en un único lugar
(buena práctica de la metodología "12-factor app").
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Ruta ABSOLUTA al archivo backend/.env. Usarla (en vez de ".env" relativo) hace
# que la configuración se cargue correctamente sin importar desde qué carpeta se
# ejecute el proceso: la app (uvicorn), Alembic o el scraper.
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Esquema tipado de toda la configuración del backend."""

    # --- Base de datos ---
    DATABASE_URL: str

    # --- Google Gemini ---
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # --- Aplicación ---
    APP_NAME: str = "PlaneAI UdeA"
    APP_ENV: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173"

    # Lee automáticamente el archivo backend/.env (ruta absoluta _ENV_FILE).
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Convierte la cadena 'a,b,c' de orígenes CORS en una lista de Python."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """
    Devuelve una ÚNICA instancia de Settings (patrón singleton vía caché).

    Gracias a @lru_cache no volvemos a leer el archivo .env en cada
    petición: se lee una sola vez y se reutiliza.
    """
    return Settings()
