"""
Capa de acceso a la base de datos.

Centraliza la creación de conexiones SQLite y la inicialización del
esquema. El resto del proyecto (routes/services) nunca abre conexiones
por su cuenta ni concatena SQL: todo pasa por aquí y usa siempre
consultas parametrizadas.
"""
import sqlite3
from pathlib import Path
from flask import g, current_app

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_db():
    """
    Devuelve la conexión SQLite asociada al contexto de la request actual
    (patrón estándar de Flask: una conexión por request, reutilizada si
    ya se pidió antes dentro de la misma request, y cerrada al final).
    """
    if "db" not in g:
        db_path = current_app.config["DATABASE_PATH"]
        # check_same_thread=False es seguro aquí porque Flask crea una
        # conexión nueva por request (via g), no se comparte entre threads.
        # isolation_level=None pone la conexión en modo autocommit real,
        # para que podamos controlar manualmente BEGIN IMMEDIATE / COMMIT
        # / ROLLBACK en vez de depender de la gestión implícita de
        # transacciones de Python (que solo usa BEGIN DEFERRED).
        g.db = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        # busy_timeout hace que, si otra conexión tiene un lock de
        # escritura, SQLite espere en lugar de fallar inmediatamente con
        # "database is locked". Es clave para el manejo de concurrencia.
        g.db.execute("PRAGMA busy_timeout = 5000")
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Crea las tablas si no existen. Se llama una vez al arrancar la app."""
    with app.app_context():
        db = get_db()
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            db.executescript(f.read())
        db.commit()
    app.teardown_appcontext(close_db)


def begin_immediate(db):
    """
    Inicia una transacción con lock de escritura inmediato.

    Por qué: por defecto, sqlite3 en modo autocommit=False empieza
    transacciones en modo DEFERRED, que solo toma el lock de escritura en
    el primer INSERT/UPDATE. Si dos requests concurrentes leen stock
    "al mismo tiempo" antes de que ninguna haya escrito, ambas pueden ver
    stock=1 y ambas decidir que hay stock suficiente (race condition
    clásica de "check-then-act").

    BEGIN IMMEDIATE toma el lock de escritura al inicio de la transacción,
    así que si dos requests intentan vender el mismo producto a la vez,
    la segunda espera (hasta busy_timeout) a que la primera termine, y
    cuando le toca su turno ve el stock ya actualizado.
    """
    db.execute("BEGIN IMMEDIATE")
