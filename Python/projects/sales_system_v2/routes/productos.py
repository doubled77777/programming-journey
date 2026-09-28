import logging
from flask import Blueprint, request, jsonify

from database.database import get_db
from services.auth_service import login_required, role_required
from services.validators import (
    ValidationError, require_fields, validate_nombre, validate_precio, validate_stock,
)

logger = logging.getLogger("sales_system")

productos_bp = Blueprint("productos", __name__, url_prefix="/productos")


def _serialize(row):
    return {
        "id": row["id"],
        "nombre": row["nombre"],
        "descripcion": row["descripcion"],
        "precio": row["precio"],
        "stock": row["stock"],
        "categoria": row["categoria"],
        "activo": bool(row["activo"]),
        "fecha_creacion": row["fecha_creacion"],
    }


@productos_bp.get("")
@login_required
def listar_productos():
    """Lista productos. Por defecto solo los activos; ?incluir_inactivos=true
    para ver todos (útil para administración)."""
    incluir_inactivos = request.args.get("incluir_inactivos", "false").lower() == "true"
    categoria = request.args.get("categoria")

    db = get_db()
    query = "SELECT * FROM productos WHERE 1=1"
    params = []
    if not incluir_inactivos:
        query += " AND activo = 1"
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    query += " ORDER BY nombre"

    rows = db.execute(query, params).fetchall()
    return jsonify([_serialize(r) for r in rows]), 200


@productos_bp.get("/<int:producto_id>")
@login_required
def obtener_producto(producto_id):
    db = get_db()
    row = db.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify(_serialize(row)), 200


@productos_bp.post("")
@role_required("ADMIN")
def crear_producto():
    data = request.get_json(silent=True)
    require_fields(data, ["nombre", "precio", "stock"])

    nombre = validate_nombre(data["nombre"])
    precio = validate_precio(data["precio"])
    stock = validate_stock(data["stock"])
    descripcion = data.get("descripcion")
    categoria = data.get("categoria")

    db = get_db()
    cursor = db.execute(
        "INSERT INTO productos (nombre, descripcion, precio, stock, categoria) "
        "VALUES (?, ?, ?, ?, ?)",
        (nombre, descripcion, precio, stock, categoria),
    )
    db.commit()
    logger.info("Producto creado id=%s nombre=%s", cursor.lastrowid, nombre)

    row = db.execute("SELECT * FROM productos WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(_serialize(row)), 201


@productos_bp.put("/<int:producto_id>")
@role_required("ADMIN")
def actualizar_producto(producto_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("El cuerpo de la solicitud debe ser un objeto JSON")

    db = get_db()
    row = db.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Producto no encontrado"}), 404

    nombre = validate_nombre(data["nombre"]) if "nombre" in data else row["nombre"]
    precio = validate_precio(data["precio"]) if "precio" in data else row["precio"]
    stock = validate_stock(data["stock"]) if "stock" in data else row["stock"]
    descripcion = data.get("descripcion", row["descripcion"])
    categoria = data.get("categoria", row["categoria"])
    activo = bool(data.get("activo", row["activo"]))

    db.execute(
        "UPDATE productos SET nombre=?, descripcion=?, precio=?, stock=?, "
        "categoria=?, activo=? WHERE id=?",
        (nombre, descripcion, precio, stock, categoria, int(activo), producto_id),
    )
    db.commit()
    logger.info("Producto actualizado id=%s", producto_id)

    row = db.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    return jsonify(_serialize(row)), 200


@productos_bp.delete("/<int:producto_id>")
@role_required("ADMIN")
def eliminar_producto(producto_id):
    """
    Baja lógica (no DELETE físico): un producto puede estar referenciado
    en ventas históricas por producto_id, así que borrarlo de verdad
    rompería la integridad/consultabilidad del historial. Se marca
    activo=0 en su lugar.
    """
    db = get_db()
    row = db.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Producto no encontrado"}), 404

    db.execute("UPDATE productos SET activo = 0 WHERE id = ?", (producto_id,))
    db.commit()
    logger.info("Producto desactivado id=%s", producto_id)
    return jsonify({"mensaje": "Producto desactivado"}), 200
