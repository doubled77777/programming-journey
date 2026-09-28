import logging
import sqlite3
from flask import Blueprint, request, jsonify

from database.database import get_db
from services.auth_service import login_required, role_required
from services.validators import ValidationError, require_fields, validate_nombre, validate_email

logger = logging.getLogger("sales_system")

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")


def _serialize(row):
    return {
        "id": row["id"],
        "nombre": row["nombre"],
        "email": row["email"],
        "telefono": row["telefono"],
        "fecha_creacion": row["fecha_creacion"],
        "activo": bool(row["activo"]),
    }


@clientes_bp.get("")
@login_required
def listar_clientes():
    incluir_inactivos = request.args.get("incluir_inactivos", "false").lower() == "true"
    db = get_db()
    query = "SELECT * FROM clientes"
    if not incluir_inactivos:
        query += " WHERE activo = 1"
    query += " ORDER BY nombre"
    rows = db.execute(query).fetchall()
    return jsonify([_serialize(r) for r in rows]), 200


@clientes_bp.get("/<int:cliente_id>")
@login_required
def obtener_cliente(cliente_id):
    db = get_db()
    row = db.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Cliente no encontrado"}), 404
    return jsonify(_serialize(row)), 200


@clientes_bp.post("")
@login_required
def crear_cliente():
    data = request.get_json(silent=True)
    require_fields(data, ["nombre", "email"])

    nombre = validate_nombre(data["nombre"])
    email = validate_email(data["email"])
    telefono = data.get("telefono")

    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO clientes (nombre, email, telefono) VALUES (?, ?, ?)",
            (nombre, email, telefono),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Ya existe un cliente con ese email"}), 409

    logger.info("Cliente creado id=%s", cursor.lastrowid)
    row = db.execute("SELECT * FROM clientes WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(_serialize(row)), 201


@clientes_bp.put("/<int:cliente_id>")
@role_required("ADMIN")
def actualizar_cliente(cliente_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("El cuerpo de la solicitud debe ser un objeto JSON")

    db = get_db()
    row = db.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Cliente no encontrado"}), 404

    nombre = validate_nombre(data["nombre"]) if "nombre" in data else row["nombre"]
    email = validate_email(data["email"]) if "email" in data else row["email"]
    telefono = data.get("telefono", row["telefono"])
    activo = bool(data.get("activo", row["activo"]))

    try:
        db.execute(
            "UPDATE clientes SET nombre=?, email=?, telefono=?, activo=? WHERE id=?",
            (nombre, email, telefono, int(activo), cliente_id),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Ya existe un cliente con ese email"}), 409

    logger.info("Cliente actualizado id=%s", cliente_id)
    row = db.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    return jsonify(_serialize(row)), 200


@clientes_bp.delete("/<int:cliente_id>")
@role_required("ADMIN")
def eliminar_cliente(cliente_id):
    db = get_db()
    row = db.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Cliente no encontrado"}), 404

    db.execute("UPDATE clientes SET activo = 0 WHERE id = ?", (cliente_id,))
    db.commit()
    logger.info("Cliente desactivado id=%s", cliente_id)
    return jsonify({"mensaje": "Cliente desactivado"}), 200
