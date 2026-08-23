import sqlite3

conexion = sqlite3.connect(
    "Python/projects/sales_system/database/sales.db"
)

cursor = conexion.cursor()


# Crear tabla de productos
cursor.execute("""
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    precio REAL NOT NULL
)
""")


# Crear tabla de ventas
cursor.execute("""
CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER,
    cantidad INTEGER,
    total REAL,
    fecha TEXT
)
""")


# Agregar productos iniciales
cursor.execute("""
INSERT OR IGNORE INTO productos (id, nombre, precio)
VALUES (1, 'Laptop', 2500)
""")

cursor.execute("""
INSERT OR IGNORE INTO productos (id, nombre, precio)
VALUES (2, 'Mouse', 80)
""")

cursor.execute("""
INSERT OR IGNORE INTO productos (id, nombre, precio)
VALUES (3, 'Teclado', 150)
""")


# Corregir precio del Mouse
cursor.execute("""
UPDATE productos
SET precio = 80
WHERE id = 2
""")


conexion.commit()


# Comprobar productos
cursor.execute("SELECT * FROM productos")

productos = cursor.fetchall()

print("Productos encontrados:")
print(productos)


conexion.close()