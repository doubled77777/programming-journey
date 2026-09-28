"""
Servicio de autenticación y autorización.

Autenticación: ¿quién sos? -> login con email/password, sesión de Flask.
Autorización:  ¿qué podés hacer? -> decoradores que revisan el rol
guardado en la sesión.

Se usa el sistema de sesiones de Flask (cookie firmada con SECRET_KEY,
del lado del servidor solo se guarda el user_id y el rol) en vez de JWT
porque no hay necesidad de que la sesión sea válida entre distintos
servicios/dominios: es un backend monolítico con su propio frontend.
"""
from functools import wraps
from flask import session, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

from database.database import get_db

ROLES = ("ADMIN", "VENDEDOR")


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password, password_hash):
    return check_password_hash(password_hash, password)


def find_user_by_email(email):
    db = get_db()
    row = db.execute(
        "SELECT * FROM usuarios WHERE email = ?", (email,)
    ).fetchone()
    return row


def find_user_by_id(user_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM usuarios WHERE id = ?", (user_id,)
    ).fetchone()
    return row


def login_required(view_func):
    """Exige que exista una sesión activa. No verifica rol (eso es
    responsabilidad de role_required)."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "No autenticado. Inicie sesión."}), 401

        user = find_user_by_id(user_id)
        if user is None or not user["activo"]:
            session.clear()
            return jsonify({"error": "Sesión inválida o usuario inactivo."}), 401

        # Deja al usuario autenticado disponible durante la request.
        g.current_user = user
        return view_func(*args, **kwargs)

    return wrapped


def role_required(*roles_permitidos):
    """
    Exige sesión activa Y que el rol del usuario esté entre los permitidos.
    Debe usarse siempre DESPUÉS de @login_required en el orden de
    decoradores (más cerca de la función = login_required).
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(*args, **kwargs):
            if g.current_user["rol"] not in roles_permitidos:
                return jsonify({
                    "error": "No tiene permisos para realizar esta acción."
                }), 403
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
