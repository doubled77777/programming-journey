"""
Configuración de logging.

Importante: nunca se loguean tokens, el access token de Mercado Pago, ni
ningún dato de tarjeta. Los logs registran QUÉ pasó (aprobado/rechazado,
producto, cantidad, order_id) para poder investigar incidentes, nunca datos
sensibles.
"""
import logging

from config import Config


def configurar_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(Config.LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
