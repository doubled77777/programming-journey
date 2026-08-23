import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "sales.db"

conexion = sqlite3.connect(DB_PATH)

cursor = conexion.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    precio REAL NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER,
    cantidad INTEGER,
    total REAL,
    fecha TEXT
)
""")


cursor.execute("""
INSERT OR IGNORE INTO productos
(id, nombre, precio, stock)
VALUES (1, 'Laptop', 2500, 10)
""")

cursor.execute("""
INSERT OR IGNORE INTO productos
(id, nombre, precio, stock)
VALUES (2, 'Mouse', 80, 30)
""")

cursor.execute("""
INSERT OR IGNORE INTO productos
(id, nombre, precio, stock)
VALUES (3, 'Teclado', 150, 20)
""")


conexion.commit()


cursor.execute("SELECT * FROM productos")

productos = cursor.fetchall()

print("Productos encontrados:")
print(productos)

conexion.close()