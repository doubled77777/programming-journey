import logging
from flask import Blueprint, request, jsonify, g

from services.auth_service import login_required, role_required
from services.validators import ValidationError, require_fields
from services.venta_service import crear_venta, listar_ventas, obtener_venta, VentaError

logger = logging.getLogger("sales_system")

ventas_bp = Blueprint("ventas", __name__, url_prefix="/ventas")


@ventas_bp.post("")
@role_required("ADMIN", "VENDEDOR")
def registrar_venta():
    data = request.get_json(silent=True)
    require_fields(data, ["cliente_id", "items"])

    # Clave de idempotencia opcional: si el cliente HTTP la manda (ej. un
    # UUID generado una sola vez por intento de "confirmar compra" en el
    # frontend), un reintento con la misma clave no crea una segunda venta.
    idempotency_key = request.headers.get("Idempotency-Key")

    try:
        body, status_code, fue_repetida = crear_venta(
            cliente_id=data["cliente_id"],
            items=data["items"],
            usuario_id=g.current_user["id"],
            idempotency_key=idempotency_key,
        )
    except VentaError as e:
        return jsonify({"error": e.message}), e.status_code

    if fue_repetida:
        logger.info(
            "Solicitud de venta duplicada detectada (idempotency_key=%s), "
            "devolviendo venta id=%s ya existente", idempotency_key, body.get("id"),
        )
    else:
        logger.info(
            "Venta creada id=%s usuario_id=%s total=%s",
            body.get("id"), g.current_user["id"], body.get("total"),
        )

    return jsonify(body), status_code


@ventas_bp.get("")
@login_required
def listar():
    cliente_id = request.args.get("cliente_id", type=int)
    ventas = listar_ventas(
        cliente_id=cliente_id,
        usuario_id=g.current_user["id"],
        rol=g.current_user["rol"],
    )
    return jsonify(ventas), 200


@ventas_bp.get("/<int:venta_id>")
@login_required
def obtener(venta_id):
    venta = obtener_venta(venta_id, usuario_id=g.current_user["id"], rol=g.current_user["rol"])
    if venta is None:
        return jsonify({"error": "Venta no encontrada"}), 404
    if venta == "forbidden":
        return jsonify({"error": "No tiene permiso para ver esta venta"}), 403
    return jsonify(venta), 200
