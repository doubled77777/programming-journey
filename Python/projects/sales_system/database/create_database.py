import sqlite3

conexion = sqlite3.connect(
    "Python/projects/sales_system/database/sales.db"
)

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    precio REAL NOT NULL
)
""")

cursor.execute("""
INSERT INTO productos (nombre, precio)
VALUES ('Laptop', 2500)
""")

conexion.commit()

cursor.execute("SELECT * FROM productos")

productos = cursor.fetchall()

print("Productos encontrados:")
print(productos)

conexion.close()