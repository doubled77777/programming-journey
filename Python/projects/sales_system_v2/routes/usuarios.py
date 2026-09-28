import logging
import sqlite3
from flask import Blueprint, request, jsonify

from database.database import get_db
from services.auth_service import role_required, hash_password, ROLES
from services.validators import ValidationError, require_fields, validate_nombre, validate_email

logger = logging.getLogger("sales_system")

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


def _serialize(row):
    # Nunca se devuelve password_hash en una respuesta de la API.
    return {
        "id": row["id"],
        "nombre": row["nombre"],
        "email": row["email"],
        "rol": row["rol"],
        "activo": bool(row["activo"]),
        "fecha_creacion": row["fecha_creacion"],
    }


@usuarios_bp.get("")
@role_required("ADMIN")
def listar_usuarios():
    db = get_db()
    rows = db.execute("SELECT * FROM usuarios ORDER BY nombre").fetchall()
    return jsonify([_serialize(r) for r in rows]), 200


@usuarios_bp.post("")
@role_required("ADMIN")
def crear_usuario():
    data = request.get_json(silent=True)
    require_fields(data, ["nombre", "email", "password", "rol"])

    nombre = validate_nombre(data["nombre"])
    email = validate_email(data["email"])
    password = data["password"]
    rol = data["rol"]

    if not isinstance(password, str) or len(password) < 6:
        raise ValidationError(
            "La contraseña debe tener al menos 6 caracteres", field="password"
        )
    if rol not in ROLES:
        raise ValidationError(f"El rol debe ser uno de: {', '.join(ROLES)}", field="rol")

    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (?, ?, ?, ?)",
            (nombre, email, hash_password(password), rol),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Ya existe un usuario con ese email"}), 409

    logger.info("Usuario creado id=%s rol=%s", cursor.lastrowid, rol)
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(_serialize(row)), 201


@usuarios_bp.put("/<int:usuario_id>")
@role_required("ADMIN")
def actualizar_usuario(usuario_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("El cuerpo de la solicitud debe ser un objeto JSON")

    db = get_db()
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Usuario no encontrado"}), 404

    nombre = validate_nombre(data["nombre"]) if "nombre" in data else row["nombre"]
    rol = data.get("rol", row["rol"])
    if rol not in ROLES:
        raise ValidationError(f"El rol debe ser uno de: {', '.join(ROLES)}", field="rol")
    activo = bool(data.get("activo", row["activo"]))

    db.execute(
        "UPDATE usuarios SET nombre=?, rol=?, activo=? WHERE id=?",
        (nombre, rol, int(activo), usuario_id),
    )
    db.commit()
    logger.info("Usuario actualizado id=%s", usuario_id)
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return jsonify(_serialize(row)), 200
