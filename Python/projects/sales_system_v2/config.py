"""
Configuración centralizada de la aplicación.
Todos los valores sensibles o dependientes del entorno se leen desde
variables de entorno (ver .env.example). Nunca se deben hardcodear
secretos en el código fuente.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Carga variables desde un archivo .env si existe (no falla si no existe).
load_dotenv(BASE_DIR / ".env")


class Config:
    # SECRET_KEY firma las cookies de sesión de Flask. Si no está definida
    # en el entorno, se genera una aleatoria en cada arranque SOLO para
    # facilitar pruebas locales rápidas; en producción SIEMPRE debe
    # definirse explícitamente vía variable de entorno.
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(32).hex()

    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH", str(BASE_DIR / "database" / "sales.db")
    )

    # Duración de la sesión de login (en minutos).
    SESSION_LIFETIME_MINUTES = int(os.environ.get("SESSION_LIFETIME_MINUTES", "60"))

    # Entorno de ejecución: development | testing | production
    ENV = os.environ.get("FLASK_ENV", "development")

    # Cookies de sesión: en producción deben viajar solo por HTTPS.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = ENV == "production"


class TestConfig(Config):
    DATABASE_PATH = ":memory:"
    SECRET_KEY = "test-secret-key-not-for-production"
    ENV = "testing"
