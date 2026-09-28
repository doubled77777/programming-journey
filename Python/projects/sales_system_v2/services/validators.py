"""
Validadores compartidos. Centralizar esto evita duplicar reglas de
negocio (ej. qué es un email válido) en cada archivo de rutas.
"""
import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(Exception):
    """Error de validación de datos de entrada -> siempre HTTP 400."""

    def __init__(self, message, field=None):
        super().__init__(message)
        self.message = message
        self.field = field


def require_fields(data, fields):
    if not isinstance(data, dict):
        raise ValidationError("El cuerpo de la solicitud debe ser un objeto JSON")
    faltantes = [f for f in fields if f not in data or data[f] in (None, "")]
    if faltantes:
        raise ValidationError(f"Faltan campos requeridos: {', '.join(faltantes)}")


def validate_email(email):
    if not isinstance(email, str) or not EMAIL_REGEX.match(email.strip()):
        raise ValidationError("El email no tiene un formato válido", field="email")
    return email.strip().lower()


def validate_nombre(nombre, field="nombre"):
    if not isinstance(nombre, str) or len(nombre.strip()) == 0:
        raise ValidationError(f"El campo '{field}' no puede estar vacío", field=field)
    return nombre.strip()


def validate_precio(precio):
    if isinstance(precio, bool) or not isinstance(precio, (int, float)):
        raise ValidationError("El precio debe ser numérico", field="precio")
    if precio < 0:
        raise ValidationError("El precio no puede ser negativo", field="precio")
    return float(precio)


def validate_stock(stock):
    if isinstance(stock, bool) or not isinstance(stock, int):
        raise ValidationError("El stock debe ser un número entero", field="stock")
    if stock < 0:
        raise ValidationError("El stock no puede ser negativo", field="stock")
    return stock


def validate_cantidad(cantidad):
    if isinstance(cantidad, bool) or not isinstance(cantidad, int):
        raise ValidationError("La cantidad debe ser un número entero", field="cantidad")
    if cantidad <= 0:
        raise ValidationError("La cantidad debe ser mayor a cero", field="cantidad")
    return cantidad
