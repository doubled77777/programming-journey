import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import Config  # noqa: E402
import app as app_module  # noqa: E402


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test_sales.db"


@pytest.fixture
def client(db_path, monkeypatch):
    """
    Cada test corre contra una base de datos SQLite temporal y aislada
    (nunca contra database/sales.db), con un producto de prueba con stock=5.
    """
    monkeypatch.setattr(Config, "DB_PATH", db_path)

    conexion = sqlite3.connect(db_path)
    conexion.execute("""
        CREATE TABLE productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL CHECK (precio >= 0),
            stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0)
        )
    """)
    conexion.execute("""
        CREATE TABLE ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL CHECK (cantidad > 0),
            total REAL NOT NULL,
            fecha TEXT NOT NULL DEFAULT (datetime('now')),
            order_id TEXT,
            client_request_id TEXT,
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    """)
    conexion.execute(
        "CREATE UNIQUE INDEX idx_ventas_client_request_id "
        "ON ventas (client_request_id) WHERE client_request_id IS NOT NULL"
    )
    conexion.execute(
        "INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
        ("Producto de prueba", 100.0, 5)
    )
    conexion.commit()
    conexion.close()

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client
