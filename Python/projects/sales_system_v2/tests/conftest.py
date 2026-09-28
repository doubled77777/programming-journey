import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app import create_app
from config import TestConfig
from database.database import get_db
from services.auth_service import hash_password


@pytest.fixture
def app():
    """
    Cada test recibe una app Flask nueva con su propia base de datos
    SQLite en un archivo temporal, completamente aislada de otros tests
    y del archivo sales.db real usado en desarrollo.

    Nota: no se usa ":memory:" aquí a propósito. Flask abre una conexión
    SQLite nueva por request (ver get_db), y una base ":memory:" vive
    solo dentro de la conexión que la creó: la segunda request abriría
    una base en memoria completamente distinta y vacía. Un archivo
    temporal real sí es compartido correctamente entre requests.
    """
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    class _TestConfig(TestConfig):
        DATABASE_PATH = db_path

    application = create_app(_TestConfig)
    yield application

    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seed_basico(app):
    """Crea un admin, un vendedor, un cliente y dos productos básicos."""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (?, ?, ?, ?)",
            ("Admin", "admin@test.com", hash_password("Admin123!"), "ADMIN"),
        )
        db.execute(
            "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (?, ?, ?, ?)",
            ("Vendedor", "vendedor@test.com", hash_password("Vendedor123!"), "VENDEDOR"),
        )
        db.execute(
            "INSERT INTO clientes (nombre, email, telefono) VALUES (?, ?, ?)",
            ("Cliente Test", "cliente@test.com", "555-0000"),
        )
        db.execute(
            "INSERT INTO productos (nombre, descripcion, precio, stock, categoria) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Producto A", "desc A", 10.0, 5, "General"),
        )
        db.execute(
            "INSERT INTO productos (nombre, descripcion, precio, stock, categoria) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Producto Único", "solo queda 1", 20.0, 1, "General"),
        )
        db.commit()
    return {
        "admin": {"email": "admin@test.com", "password": "Admin123!"},
        "vendedor": {"email": "vendedor@test.com", "password": "Vendedor123!"},
        "cliente_id": 1,
        "producto_a_id": 1,
        "producto_unico_id": 2,
    }


def login(client, email, password):
    return client.post("/auth/login", json={"email": email, "password": password})
