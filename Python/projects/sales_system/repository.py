"""
Capa de acceso a datos.

Separa "cómo se guardan/leen las cosas en SQLite" de "cómo responde la API"
(eso vive en app.py). Esto es lo que permite, por ejemplo, testear las reglas
de negocio (stock, ventas) sin tener que levantar Flask, y probar los
endpoints sin preocuparse por el detalle de las consultas SQL.
"""
import sqlite3

from config import Config
from db import get_db_connection


class StockInsuficienteError(Exception):
    """El stock no alcanzaba en el momento exacto de confirmar la venta."""
    pass


# ---------------------------------------------------------------------------
# Productos
# ---------------------------------------------------------------------------

def listar_productos():
    conexion = get_db_connection()
    try:
        filas = conexion.execute(
            "SELECT id, nombre, precio, stock FROM productos ORDER BY id"
        ).fetchall()
        return [dict(fila) for fila in filas]
    finally:
        conexion.close()


def obtener_producto(producto_id):
    conexion = get_db_connection()
    try:
        fila = conexion.execute(
            "SELECT id, nombre, precio, stock FROM productos WHERE id = ?",
            (producto_id,)
        ).fetchone()
        return dict(fila) if fila else None
    finally:
        conexion.close()


def crear_producto(nombre, precio, stock):
    conexion = get_db_connection()
    try:
        cursor = conexion.execute(
            "INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
            (nombre, precio, stock)
        )
        conexion.commit()
        return cursor.lastrowid
    finally:
        conexion.close()


def actualizar_producto(producto_id, nombre=None, precio=None, stock=None):
    conexion = get_db_connection()
    try:
        producto = conexion.execute(
            "SELECT * FROM productos WHERE id = ?", (producto_id,)
        ).fetchone()
        if producto is None:
            return False

        nuevo_nombre = nombre if nombre is not None else producto["nombre"]
        nuevo_precio = precio if precio is not None else producto["precio"]
        nuevo_stock = stock if stock is not None else producto["stock"]

        conexion.execute(
            "UPDATE productos SET nombre = ?, precio = ?, stock = ? WHERE id = ?",
            (nuevo_nombre, nuevo_precio, nuevo_stock, producto_id)
        )
        conexion.commit()
        return True
    finally:
        conexion.close()


def eliminar_producto(producto_id):
    conexion = get_db_connection()
    try:
        cursor = conexion.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
        conexion.commit()
        return cursor.rowcount > 0
    finally:
        conexion.close()


# ---------------------------------------------------------------------------
# Ventas
# ---------------------------------------------------------------------------

def buscar_venta_por_client_request_id(client_request_id):
    conexion = get_db_connection()
    try:
        fila = conexion.execute(
            "SELECT * FROM ventas WHERE client_request_id = ?",
            (client_request_id,)
        ).fetchone()
        return dict(fila) if fila else None
    finally:
        conexion.close()


def listar_ventas():
    conexion = get_db_connection()
    try:
        filas = conexion.execute(
            """
            SELECT ventas.id, ventas.producto_id, productos.nombre AS producto_nombre,
                   ventas.cantidad, ventas.total, ventas.fecha, ventas.order_id
            FROM ventas
            JOIN productos ON productos.id = ventas.producto_id
            ORDER BY ventas.id DESC
            """
        ).fetchall()
        return [dict(fila) for fila in filas]
    finally:
        conexion.close()


def registrar_venta_y_descontar_stock(producto_id, cantidad, total, order_id, client_request_id):
    """
    Registra una venta y descuenta el stock de forma atómica y segura ante
    concurrencia.

    Dos mecanismos distintos, para dos problemas distintos:

    1. Concurrencia (evitar vender más stock del que hay): el descuento de
       stock se hace con una única sentencia
           UPDATE productos SET stock = stock - ? WHERE id = ? AND stock >= ?
       en vez de "leer el stock" y luego "escribir el nuevo valor" como dos
       pasos separados. SQLite ejecuta esa sentencia como una operación
       indivisible a nivel de motor: dos requests concurrentes no pueden
       leer el mismo stock "viejo" y descontar ambas por separado, porque
       ninguna de las dos está "leyendo" un valor por su cuenta - cada una
       le pide directamente al motor "réstame esto SI ALCANZA", y SQLite
       serializa esa operación internamente.

    2. Atomicidad/consistencia (que la venta y el descuento de stock ocurran
       juntos, o ninguno de los dos): se usa BEGIN IMMEDIATE para adquirir el
       bloqueo de escritura antes de tocar nada, y solo se hace COMMIT si
       tanto el UPDATE como el INSERT terminaron bien. Si algo falla en el
       medio, ROLLBACK deshace todo, incluyendo el descuento de stock.

    Lanza StockInsuficienteError si, en el momento exacto del UPDATE, ya no
    había stock suficiente (por ejemplo, porque otra venta concurrente se
    adelantó). Quien llama a esta función debe decidir qué hacer en ese caso
    (en nuestro caso: el pago con Mercado Pago ya se aprobó, así que hay que
    registrar el incidente para revisión manual, no solo devolver un error).
    """
    conexion = sqlite3.connect(Config.DB_PATH)
    conexion.row_factory = sqlite3.Row
    conexion.isolation_level = None  # control manual y explícito de BEGIN/COMMIT/ROLLBACK
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.execute("PRAGMA busy_timeout = 5000")

    try:
        conexion.execute("BEGIN IMMEDIATE")

        cursor = conexion.execute(
            "UPDATE productos SET stock = stock - ? WHERE id = ? AND stock >= ?",
            (cantidad, producto_id, cantidad)
        )

        if cursor.rowcount == 0:
            conexion.execute("ROLLBACK")
            raise StockInsuficienteError(
                f"Stock insuficiente para el producto {producto_id} al confirmar la venta"
            )

        conexion.execute(
            """
            INSERT INTO ventas (producto_id, cantidad, total, fecha, order_id, client_request_id)
            VALUES (?, ?, ?, datetime('now'), ?, ?)
            """,
            (producto_id, cantidad, total, order_id, client_request_id)
        )

        conexion.execute("COMMIT")
    except sqlite3.IntegrityError:
        conexion.execute("ROLLBACK")
        raise
    except StockInsuficienteError:
        raise
    except Exception:
        conexion.execute("ROLLBACK")
        raise
    finally:
        conexion.close()
