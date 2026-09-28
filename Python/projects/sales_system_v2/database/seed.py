"""
Script para poblar la base de datos con datos iniciales de prueba:
usuarios (admin/vendedor), clientes y productos.

Uso:
    python -m database.seed

Es idempotente: si un registro ya existe (mismo email), no lo duplica.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from database.database import get_db, init_db
from services.auth_service import hash_password

PRODUCTOS = [
    ("Laptop 14\" Core i5", "Laptop para oficina, 8GB RAM, 256GB SSD", 650.00, 15, "Computación"),
    ("Mouse inalámbrico", "Mouse óptico inalámbrico 2.4GHz", 12.50, 80, "Accesorios"),
    ("Teclado mecánico", "Teclado mecánico switches rojos, retroiluminado", 45.00, 30, "Accesorios"),
    ("Monitor 24\" Full HD", "Monitor LED 24 pulgadas, 75Hz", 145.00, 20, "Computación"),
    ("Auriculares Bluetooth", "Auriculares over-ear con cancelación de ruido", 55.00, 40, "Audio"),
    ("Webcam HD 1080p", "Webcam USB con micrófono integrado", 28.00, 3, "Accesorios"),
    ("Disco SSD 1TB", "Disco de estado sólido SATA III", 70.00, 25, "Almacenamiento"),
    ("Silla ergonómica", "Silla de oficina con soporte lumbar ajustable", 180.00, 10, "Mobiliario"),
]

CLIENTES = [
    ("Ana Torres", "ana.torres@example.com", "555-1001"),
    ("Bruno Gómez", "bruno.gomez@example.com", "555-1002"),
    ("Carla Ruiz", "carla.ruiz@example.com", "555-1003"),
]

USUARIOS = [
    ("Administrador", "admin@sistema.com", "Admin123!", "ADMIN"),
    ("Vendedor Uno", "vendedor@sistema.com", "Vendedor123!", "VENDEDOR"),
]


def seed():
    app = create_app()
    with app.app_context():
        db = get_db()

        for nombre, email, password, rol in USUARIOS:
            existente = db.execute(
                "SELECT id FROM usuarios WHERE email = ?", (email,)
            ).fetchone()
            if existente is None:
                db.execute(
                    "INSERT INTO usuarios (nombre, email, password_hash, rol) "
                    "VALUES (?, ?, ?, ?)",
                    (nombre, email, hash_password(password), rol),
                )
                print(f"Usuario creado: {email} ({rol})")

        for nombre, email, telefono in CLIENTES:
            existente = db.execute(
                "SELECT id FROM clientes WHERE email = ?", (email,)
            ).fetchone()
            if existente is None:
                db.execute(
                    "INSERT INTO clientes (nombre, email, telefono) VALUES (?, ?, ?)",
                    (nombre, email, telefono),
                )
                print(f"Cliente creado: {nombre}")

        for nombre, descripcion, precio, stock, categoria in PRODUCTOS:
            existente = db.execute(
                "SELECT id FROM productos WHERE nombre = ?", (nombre,)
            ).fetchone()
            if existente is None:
                db.execute(
                    "INSERT INTO productos (nombre, descripcion, precio, stock, categoria) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (nombre, descripcion, precio, stock, categoria),
                )
                print(f"Producto creado: {nombre}")

        db.commit()
        print("\nDatos de prueba listos.")
        print("Credenciales de prueba:")
        for nombre, email, password, rol in USUARIOS:
            print(f"  {rol}: {email} / {password}")


if __name__ == "__main__":
    seed()
