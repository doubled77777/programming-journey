"""
Conexión a la base de datos.

Centralizado aquí para que todos los módulos (repository.py, scripts de
migración, tests) usen exactamente la misma forma de conectarse, en vez de
repetir sqlite3.connect(...) con configuraciones ligeramente distintas en
cada archivo.
"""
import sqlite3

from config import Config


def get_db_connection():
    conexion = sqlite3.connect(Config.DB_PATH)
    conexion.row_factory = sqlite3.Row  # permite acceder a columnas por nombre
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.execute("PRAGMA busy_timeout = 5000")  # espera hasta 5s si la BD está ocupada
    return conexion
