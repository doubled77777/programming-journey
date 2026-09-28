import logging
import sqlite3

from flask import Flask, jsonify, request
from flask_cors import CORS

import repository
from auth import requiere_admin
from config import Config
from logging_config import configurar_logging
from services.mercadopago_service import PaymentError, cobrar_con_mercadopago

configurar_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=Config.CORS_ORIGINS if Config.CORS_ORIGINS == "*" else Config.CORS_ORIGINS.split(","))


# ---------------------------------------------------------------------------
# Validación
# ---------------------------------------------------------------------------

def validar_datos_orden(data):
    """
    Valida el cuerpo de POST /process_order. Nunca confiamos en que el
    frontend ya validó esto - un cliente HTTP cualquiera (curl, Postman, un
    bot) puede saltarse el frontend por completo.
    """
    if data is None:
        return ["El cuerpo de la solicitud debe ser JSON válido"]

    errores = []

    producto_id = data.get("producto_id")
    cantidad = data.get("cantidad")
    token = data.get("token")
    client_request_id = data.get("client_request_id")

    if producto_id is None:
        errores.append("producto_id es requerido")
    elif not isinstance(producto_id, int) or isinstance(producto_id, bool):
        errores.append("producto_id debe ser un entero")

    if cantidad is None:
        errores.append("cantidad es requerida")
    elif not isinstance(cantidad, int) or isinstance(cantidad, bool):
        errores.append("cantidad debe ser un entero")
    elif cantidad <= 0:
        errores.append("cantidad debe ser mayor a cero")

    if not token or not isinstance(token, str):
        errores.append("token de la tarjeta es requerido")

    if not client_request_id or not isinstance(client_request_id, str):
        errores.append("client_request_id es requerido (identificador único de este intento de compra)")

    return errores


def validar_datos_producto(data, parcial=False):
    errores = []
    nombre = data.get("nombre")
    precio = data.get("precio")
    stock = data.get("stock")

    if not parcial or "nombre" in data:
        if not nombre or not isinstance(nombre, str):
            errores.append("nombre es requerido y debe ser texto")

    if not parcial or "precio" in data:
        if precio is None or isinstance(precio, bool) or not isinstance(precio, (int, float)) or precio < 0:
            errores.append("precio debe ser un número mayor o igual a 0")

    if not parcial or "stock" in data:
        if stock is None or isinstance(stock, bool) or not isinstance(stock, int) or stock < 0:
            errores.append("stock debe ser un entero mayor o igual a 0")

    return errores


# ---------------------------------------------------------------------------
# Rutas públicas
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return jsonify({"status": "ok", "message": "Sales System funcionando"})


@app.route("/productos", methods=["GET"])
def obtener_productos():
    return jsonify(repository.listar_productos())


@app.route("/productos/<int:producto_id>", methods=["GET"])
def obtener_producto_por_id(producto_id):
    producto = repository.obtener_producto(producto_id)
    if producto is None:
        return jsonify({"status": "error", "message": "Producto no encontrado"}), 404
    return jsonify(producto)


@app.route("/process_order", methods=["POST"])
def process_order():
    if not request.is_json:
        return jsonify({
            "status": "error",
            "message": "Content-Type debe ser application/json"
        }), 400

    data = request.get_json(silent=True)
    errores = validar_datos_orden(data)
    if errores:
        return jsonify({"status": "error", "message": "Datos inválidos", "errores": errores}), 400

    producto_id = data["producto_id"]
    cantidad = data["cantidad"]
    client_request_id = data["client_request_id"]

    # --- Idempotencia (paso 1): si ya procesamos esta misma solicitud antes,
    # devolvemos el mismo resultado sin volver a cobrar. Esto cubre dobles
    # clics, reintentos del navegador tras un timeout, etc.
    venta_existente = repository.buscar_venta_por_client_request_id(client_request_id)
    if venta_existente:
        logger.info("Solicitud duplicada detectada (client_request_id=%s); no se vuelve a cobrar", client_request_id)
        return jsonify({
            "status": "success",
            "message": "Esta orden ya había sido procesada anteriormente",
            "total": venta_existente["total"],
            "order_id": venta_existente["order_id"],
        })

    producto = repository.obtener_producto(producto_id)
    if producto is None:
        return jsonify({"status": "error", "message": "Producto no encontrado"}), 404

    if producto["stock"] < cantidad:
        return jsonify({"status": "error", "message": "Stock insuficiente"}), 400

    total = producto["precio"] * cantidad

    try:
        resultado_pago = cobrar_con_mercadopago(data, total, idempotency_key=client_request_id)
    except PaymentError as exc:
        logger.error("Fallo de integración con Mercado Pago (client_request_id=%s): %s", client_request_id, exc)
        return jsonify({
            "status": "error",
            "message": "No se pudo procesar el pago en este momento. Intenta nuevamente."
        }), 502

    if not resultado_pago["aprobado"]:
        logger.info(
            "Pago rechazado (client_request_id=%s, status=%s, detail=%s)",
            client_request_id, resultado_pago["status"], resultado_pago["status_detail"]
        )
        return jsonify({
            "status": "error",
            "message": "El pago fue rechazado",
            "detalle": resultado_pago["status_detail"],
        }), 402

    # --- El dinero ya se movió en Mercado Pago. A partir de aquí, cualquier
    # falla debe quedar registrada de forma ruidosa: nunca perder en silencio
    # un pago aprobado que no se pudo registrar como venta.
    try:
        repository.registrar_venta_y_descontar_stock(
            producto_id, cantidad, total,
            order_id=resultado_pago["order_id"],
            client_request_id=client_request_id,
        )
    except repository.StockInsuficienteError:
        logger.critical(
            "PAGO APROBADO SIN VENTA REGISTRADA (stock agotado entre la verificación y el cobro): "
            "order_id=%s producto_id=%s cantidad=%s total=%s client_request_id=%s. "
            "Requiere revisión manual (posible reembolso).",
            resultado_pago["order_id"], producto_id, cantidad, total, client_request_id
        )
        return jsonify({
            "status": "error",
            "message": (
                "Tu pago fue procesado pero no pudimos completar tu pedido por falta de stock. "
                "Contáctanos con esta referencia para resolverlo."
            ),
            "referencia": resultado_pago["order_id"],
        }), 409
    except sqlite3.IntegrityError:
        # Dos requests con el mismo client_request_id llegaron casi al mismo tiempo
        # y ambas pasaron el chequeo de duplicado antes de que la primera terminara
        # de escribir. La restricción UNIQUE de la base de datos es la última línea
        # de defensa contra esto.
        logger.warning(
            "Venta duplicada evitada por restricción UNIQUE (client_request_id=%s)", client_request_id
        )
        venta_existente = repository.buscar_venta_por_client_request_id(client_request_id)
        return jsonify({
            "status": "success",
            "message": "Esta orden ya había sido procesada anteriormente",
            "total": venta_existente["total"] if venta_existente else total,
        })
    except Exception:
        logger.critical(
            "PAGO APROBADO SIN VENTA REGISTRADA (error inesperado de base de datos): "
            "order_id=%s producto_id=%s cantidad=%s total=%s client_request_id=%s",
            resultado_pago["order_id"], producto_id, cantidad, total, client_request_id,
            exc_info=True,
        )
        return jsonify({
            "status": "error",
            "message": (
                "Tu pago fue procesado pero ocurrió un error registrando tu pedido. "
                "Contáctanos con esta referencia para resolverlo."
            ),
            "referencia": resultado_pago["order_id"],
        }), 500

    return jsonify({
        "status": "success",
        "message": "Pago aprobado y venta registrada correctamente",
        "total": total,
        "order_id": resultado_pago["order_id"],
    })


# ---------------------------------------------------------------------------
# Rutas administrativas (requieren X-API-Key)
# ---------------------------------------------------------------------------

@app.route("/productos", methods=["POST"])
@requiere_admin
def crear_producto():
    data = request.get_json(silent=True) or {}
    errores = validar_datos_producto(data)
    if errores:
        return jsonify({"status": "error", "message": "Datos inválidos", "errores": errores}), 400

    producto_id = repository.crear_producto(data["nombre"], data["precio"], data["stock"])
    logger.info("Producto creado: id=%s nombre=%s", producto_id, data["nombre"])
    return jsonify({"status": "success", "id": producto_id}), 201


@app.route("/productos/<int:producto_id>", methods=["PUT"])
@requiere_admin
def actualizar_producto_endpoint(producto_id):
    data = request.get_json(silent=True) or {}
    errores = validar_datos_producto(data, parcial=True)
    if errores:
        return jsonify({"status": "error", "message": "Datos inválidos", "errores": errores}), 400

    actualizado = repository.actualizar_producto(
        producto_id,
        nombre=data.get("nombre"),
        precio=data.get("precio"),
        stock=data.get("stock"),
    )
    if not actualizado:
        return jsonify({"status": "error", "message": "Producto no encontrado"}), 404

    logger.info("Producto actualizado: id=%s", producto_id)
    return jsonify({"status": "success"})


@app.route("/productos/<int:producto_id>", methods=["DELETE"])
@requiere_admin
def eliminar_producto_endpoint(producto_id):
    eliminado = repository.eliminar_producto(producto_id)
    if not eliminado:
        return jsonify({"status": "error", "message": "Producto no encontrado"}), 404

    logger.info("Producto eliminado: id=%s", producto_id)
    return jsonify({"status": "success"})


@app.route("/ventas", methods=["GET"])
@requiere_admin
def obtener_ventas():
    return jsonify(repository.listar_ventas())


# ---------------------------------------------------------------------------
# Manejo de errores genéricos (no exponer detalles internos al cliente)
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_error):
    return jsonify({"status": "error", "message": "Recurso no encontrado"}), 404


@app.errorhandler(405)
def method_not_allowed(_error):
    return jsonify({"status": "error", "message": "Método no permitido para esta ruta"}), 405


@app.errorhandler(500)
def internal_error(_error):
    logger.exception("Error interno no controlado")
    return jsonify({"status": "error", "message": "Error interno del servidor"}), 500


if __name__ == "__main__":
    app.run(debug=Config.FLASK_DEBUG, port=Config.FLASK_PORT)
