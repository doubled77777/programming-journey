"""
Autenticación y autorización mínimas.

Este proyecto no tiene un sistema de usuarios con contraseñas (no hace
falta: solo existe un rol administrativo, no varios administradores con
cuentas propias). Por eso se usa el enfoque más simple que resuelve el
problema real: una API key compartida para las operaciones administrativas.

- Autenticación ("¿quién eres?"): quien envía el header X-API-Key correcto
  se identifica como administrador.
- Autorización ("¿qué puedes hacer?"): el decorador @requiere_admin protege
  las rutas que solo el administrador debe poder usar (gestión de productos,
  ver el listado de ventas). Los endpoints públicos (ver catálogo, comprar)
  no requieren ninguna credencial - son las operaciones normales de un
  cliente.

Si este proyecto creciera hasta necesitar varios administradores con
credenciales propias, sesiones, expiración de tokens, etc., el paso natural
sería migrar a JWT o a Flask-Login con una tabla de usuarios - pero eso sería
una complejidad innecesaria para lo que este sistema necesita hoy.
"""
from functools import wraps

from flask import jsonify, request

from config import Config


def requiere_admin(vista):
    @wraps(vista)
    def wrapper(*args, **kwargs):
        api_key_recibida = request.headers.get("X-API-Key")

        if not Config.ADMIN_API_KEY:
            return jsonify({
                "status": "error",
                "message": "El servidor no tiene configurada una API key de administrador (ADMIN_API_KEY en .env)"
            }), 500

        if api_key_recibida != Config.ADMIN_API_KEY:
            return jsonify({
                "status": "error",
                "message": "No autorizado. Se requiere una API key de administrador válida (header X-API-Key)."
            }), 401

        return vista(*args, **kwargs)

    return wrapper
