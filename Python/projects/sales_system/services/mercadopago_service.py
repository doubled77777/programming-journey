"""
Integración con Mercado Pago (Checkout API vía Orders).

Se eligió Orders API (en vez de la clásica Payments API) porque es la vía
"recomendada" según la documentación oficial de Mercado Pago, y porque la
aplicación de este proyecto quedó configurada bajo ese modelo (usar Payments
API generaba el error "Unauthorized use of live credentials" incluso con
credenciales de prueba correctas, por una desalineación de modelo de
integración, no de credenciales).
"""
import logging

import requests

from config import Config

logger = logging.getLogger(__name__)

MERCADOPAGO_ORDERS_URL = "https://api.mercadopago.com/v1/orders"


class PaymentError(Exception):
    """
    Error al comunicarse con Mercado Pago: timeout, problema de red, o una
    respuesta que no pudimos interpretar. Distinto de un pago RECHAZADO
    (eso no es un error de integración, es un resultado válido: la tarjeta
    fue rechazada y se maneja como tal, no como una excepción).
    """
    pass


def cobrar_con_mercadopago(datos_formulario, total, idempotency_key):
    """
    Intenta cobrar `total` usando los datos de tarjeta que entrega el Card
    Payment Brick (`datos_formulario`).

    `idempotency_key` se usa tanto como external_reference de la orden como
    en el header X-Idempotency-Key. Es importante que sea el MISMO valor en
    reintentos de la misma solicitud lógica (lo genera el frontend una vez
    por intento de compra) - así, si el request se reintenta por un timeout
    del lado del cliente, Mercado Pago reconoce que es la misma operación y
    no cobra dos veces, en vez de generar una orden nueva cada vez.

    Devuelve un dict con: aprobado (bool), order_id, status, status_detail.
    Lanza PaymentError si no se pudo completar la comunicación con Mercado
    Pago (no significa que la tarjeta fue rechazada - significa que ni
    siquiera pudimos preguntar).
    """
    headers = {
        "Authorization": f"Bearer {Config.MERCADOPAGO_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": idempotency_key
    }

    order_payload = {
        "type": "online",
        "external_reference": idempotency_key,
        "processing_mode": "automatic",
        "total_amount": f"{total:.2f}",
        "payer": {
            "email": datos_formulario.get("payer", {}).get("email", "comprador@test.com")
        },
        "transactions": {
            "payments": [
                {
                    "amount": f"{total:.2f}",
                    "payment_method": {
                        "id": datos_formulario.get("payment_method_id"),
                        "type": "credit_card",
                        "token": datos_formulario.get("token"),
                        "installments": datos_formulario.get("installments", 1)
                    }
                }
            ]
        }
    }

    try:
        response = requests.post(
            MERCADOPAGO_ORDERS_URL,
            headers=headers,
            json=order_payload,
            timeout=Config.MERCADOPAGO_TIMEOUT
        )
    except requests.exceptions.Timeout:
        logger.error("Timeout al conectar con Mercado Pago (idempotency_key=%s)", idempotency_key)
        raise PaymentError("Mercado Pago no respondió a tiempo")
    except requests.exceptions.RequestException as exc:
        logger.error("Error de red con Mercado Pago (idempotency_key=%s): %s", idempotency_key, exc)
        raise PaymentError("No se pudo conectar con Mercado Pago")

    try:
        resultado = response.json()
    except ValueError:
        logger.error(
            "Respuesta no-JSON de Mercado Pago (http=%s, idempotency_key=%s)",
            response.status_code, idempotency_key
        )
        raise PaymentError("Respuesta inválida de Mercado Pago")

    # Nunca se loguean headers ni tokens - solo el resultado del intento de cobro.
    logger.info(
        "Respuesta de Mercado Pago: http=%s status=%s status_detail=%s order_id=%s",
        response.status_code,
        resultado.get("status"),
        resultado.get("status_detail"),
        resultado.get("id"),
    )

    aprobado = resultado.get("status") == "processed"

    return {
        "aprobado": aprobado,
        "order_id": resultado.get("id"),
        "status": resultado.get("status"),
        "status_detail": resultado.get("status_detail"),
    }
