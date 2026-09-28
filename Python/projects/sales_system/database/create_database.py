"""
Script de inicialización / migración de la base de datos.

Antes, este archivo no creaba nada: era un script de prueba para verificar
que python-dotenv encontraba el token de Mercado Pago. Ahora sí cumple lo
que su nombre promete.

Es seguro ejecutarlo varias veces:
- Si la base de datos no existe, la crea completa desde cero.
- Si ya existe (como la que trae este proyecto, con datos de prueba reales),
  solo agrega las columnas/índices que falten, sin borrar nada.

Uso:
    python database/create_database.py
"""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "sales.db"


def crear_tablas(conexion):
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL CHECK (precio >= 0),
            stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0)
        )
    """)

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
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


def migrar_columnas_faltantes(conexion):
    """
    Agrega columnas nuevas a una tabla 'ventas' que ya existía antes de que
    introdujéramos order_id (para idempotencia con Mercado Pago) y
    client_request_id (para idempotencia de nuestro propio backend).
    """
    columnas_actuales = {
        fila[1] for fila in conexion.execute("PRAGMA table_info(ventas)")
    }

    if "order_id" not in columnas_actuales:
        conexion.execute("ALTER TABLE ventas ADD COLUMN order_id TEXT")
        print("Columna 'order_id' agregada a 'ventas'.")

    if "client_request_id" not in columnas_actuales:
        conexion.execute("ALTER TABLE ventas ADD COLUMN client_request_id TEXT")
        print("Columna 'client_request_id' agregada a 'ventas'.")


def crear_indices(conexion):
    conexion.execute(
        "CREATE INDEX IF NOT EXISTS idx_ventas_producto_id ON ventas (producto_id)"
    )
    # Único pero permite NULL (ventas antiguas, previas a este cambio, no tienen valor aquí)
    conexion.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_ventas_client_request_id "
        "ON ventas (client_request_id) WHERE client_request_id IS NOT NULL"
    )


def poblar_datos_de_ejemplo(conexion):
    total_productos = conexion.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
    if total_productos > 0:
        print(f"La tabla 'productos' ya tiene {total_productos} fila(s); no se insertan ejemplos.")
        return

    productos_ejemplo = [
        ("Laptop", 2500.0, 10),
        ("Mouse", 80.0, 30),
        ("Teclado", 150.0, 20),
    ]
    conexion.executemany(
        "INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
        productos_ejemplo
    )
    print(f"Se insertaron {len(productos_ejemplo)} productos de ejemplo.")


def inicializar_base_de_datos():
    conexion = sqlite3.connect(DB_PATH)
    try:
        crear_tablas(conexion)
        migrar_columnas_faltantes(conexion)
        crear_indices(conexion)
        poblar_datos_de_ejemplo(conexion)
        conexion.commit()
        print(f"Base de datos lista en: {DB_PATH}")
    finally:
        conexion.close()


if __name__ == "__main__":
    inicializar_base_de_datos()
