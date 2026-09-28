import logging
import sqlite3
from datetime import timedelta
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config import Config
from database.database import init_db
from services.validators import ValidationError
from services.venta_service import VentaError

from routes.auth import auth_bp
from routes.productos import productos_bp
from routes.clientes import clientes_bp
from routes.ventas import ventas_bp
from routes.reportes import reportes_bp
from routes.usuarios import usuarios_bp

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"


def configure_logging(app):
    logger = logging.getLogger("sales_system")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    # Silenciar logs verbosos de werkzeug en cada request salvo errores.
    logging.getLogger("werkzeug").setLevel(logging.WARNING)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.permanent_session_lifetime = timedelta(
        minutes=app.config.get("SESSION_LIFETIME_MINUTES", 60)
    )

    configure_logging(app)
    logger = logging.getLogger("sales_system")

    CORS(app, supports_credentials=True)

    init_db(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(productos_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(ventas_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(usuarios_bp)

    # ---------------------------------------------------------------
    # Manejo centralizado de errores: todas las rutas devuelven JSON
    # consistente en vez de dejar que Flask devuelva HTML por defecto,
    # y ningún detalle interno (stack trace, mensaje de excepción de
    # bajo nivel) se filtra en errores 500.
    # ---------------------------------------------------------------

    @app.errorhandler(ValidationError)
    def handle_validation_error(err):
        return jsonify({"error": err.message, "field": err.field}), 400

    @app.errorhandler(VentaError)
    def handle_venta_error(err):
        return jsonify({"error": err.message}), err.status_code

    @app.errorhandler(400)
    def handle_bad_request(err):
        return jsonify({"error": "Solicitud inválida"}), 400

    @app.errorhandler(404)
    def handle_not_found(err):
        return jsonify({"error": "Recurso no encontrado"}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(err):
        return jsonify({"error": "Método no permitido"}), 405

    @app.errorhandler(sqlite3.IntegrityError)
    def handle_integrity_error(err):
        logger.warning("Error de integridad de base de datos: %s", err)
        return jsonify({"error": "Conflicto con datos existentes"}), 409

    @app.errorhandler(sqlite3.Error)
    def handle_db_error(err):
        logger.error("Error de base de datos: %s", err)
        return jsonify({"error": "Error interno de base de datos"}), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        logger.exception("Error no controlado")
        return jsonify({"error": "Error interno del servidor"}), 500

    # ---------------------------------------------------------------
    # Frontend estático simple (HTML/CSS/JS consumiendo esta misma API).
    # ---------------------------------------------------------------
    @app.get("/")
    def serve_index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/<path:filename>")
    def serve_frontend_assets(filename):
        if (FRONTEND_DIR / filename).is_file():
            return send_from_directory(FRONTEND_DIR, filename)
        return jsonify({"error": "Recurso no encontrado"}), 404

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=(app.config["ENV"] != "production"), port=5000)
