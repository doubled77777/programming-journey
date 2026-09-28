"""
Configuración central de la aplicación.

Todo valor que pueda cambiar entre entornos (desarrollo, pruebas, producción)
vive aquí y se lee desde variables de entorno, nunca hardcodeado en el código
de negocio. Esto es lo que permite que el mismo código funcione en distintas
máquinas con distinta configuración, sin tocar una sola línea de app.py.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Config:
    # Base de datos
    DB_PATH = BASE_DIR / "database" / "sales.db"

    # Mercado Pago
    MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
    MERCADOPAGO_TIMEOUT = float(os.getenv("MERCADOPAGO_TIMEOUT", "10"))

    # Autenticación de administrador (ver auth.py)
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

    # Flask
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

    # CORS: lista de orígenes separados por coma, o "*" para desarrollo
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Logging
    LOG_FILE = BASE_DIR / "sales_system.log"
