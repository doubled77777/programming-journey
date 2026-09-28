import logging
from flask import Blueprint, request, jsonify, session

from services.auth_service import find_user_by_email, verify_password, login_required
from services.validators import ValidationError, require_fields

logger = logging.getLogger("sales_system")

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True)
    require_fields(data, ["email", "password"])

    email = data["email"].strip().lower()
    password = data["password"]

    user = find_user_by_email(email)

    # Importante: el mensaje de error es el mismo tanto si el email no
    # existe como si la contraseña es incorrecta. Distinguir ambos casos
    # le regalaría a un atacante información sobre qué emails están
    # registrados (enumeración de usuarios).
    if user is None or not user["activo"] or not verify_password(password, user["password_hash"]):
        logger.info("Intento de login fallido para email=%s", email)
        return jsonify({"error": "Email o contraseña incorrectos"}), 401

    session.clear()
    session["user_id"] = user["id"]
    session["rol"] = user["rol"]
    session.permanent = True

    logger.info("Login exitoso: usuario_id=%s rol=%s", user["id"], user["rol"])
    return jsonify({
        "id": user["id"],
        "nombre": user["nombre"],
        "email": user["email"],
        "rol": user["rol"],
    }), 200


@auth_bp.post("/logout")
@login_required
def logout():
    session.clear()
    return jsonify({"mensaje": "Sesión cerrada"}), 200


@auth_bp.get("/me")
@login_required
def me():
    from flask import g
    user = g.current_user
    return jsonify({
        "id": user["id"],
        "nombre": user["nombre"],
        "email": user["email"],
        "rol": user["rol"],
    }), 200
