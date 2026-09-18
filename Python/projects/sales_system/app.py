import os
import sqlite3
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "sales.db"

MP_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN")


def get_db_connection():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row  # permite acceder a columnas por nombre
    return conexion


def cobrar_con_mercadopago(datos_formulario, total):
    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4())
    }

    order_payload = {
        "type": "online",
        "external_reference": str(uuid.uuid4()),
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

    response = requests.post(
        "https://api.mercadopago.com/v1/orders",
        headers=headers,
        json=order_payload
    )

    resultado = response.json()

    print("Código de estado HTTP:", response.status_code)
    print("Respuesta completa de Mercado Pago:", resultado)

    aprobado = resultado.get("status") == "processed"

    return aprobado, resultado.get("status_detail")


@app.route("/")
def home():
    return "Sales System funcionando"


@app.route("/productos", methods=["GET"])
def obtener_productos():
    conexion = get_db_connection()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, precio, stock FROM productos")
    filas = cursor.fetchall()
    conexion.close()

    productos = [dict(fila) for fila in filas]
    return jsonify(productos)


@app.route("/process_order", methods=["POST"])
def process_order():
    data = request.json

    producto_id = data.get("producto_id")
    cantidad = data.get("cantidad")
    token = data.get("token")

    if producto_id is None or cantidad is None or token is None:
        return jsonify({
            "status": "error",
            "message": "Faltan datos: se requiere producto_id, cantidad y token de la tarjeta"
        }), 400

    conexion = get_db_connection()
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT precio, stock FROM productos WHERE id = ?",
        (producto_id,)
    )
    producto = cursor.fetchone()

    if producto is None:
        conexion.close()
        return jsonify({
            "status": "error",
            "message": "Producto no encontrado"
        }), 404

    if producto["stock"] < cantidad:
        conexion.close()
        return jsonify({
            "status": "error",
            "message": "Stock insuficiente"
        }), 400

    total = producto["precio"] * cantidad

    pago_aprobado, detalle_pago = cobrar_con_mercadopago(data, total)

    if not pago_aprobado:
        conexion.close()
        return jsonify({
            "status": "error",
            "message": "El pago fue rechazado",
            "detalle": detalle_pago
        }), 402

    cursor.execute(
        "INSERT INTO ventas (producto_id, cantidad, total, fecha) VALUES (?, ?, ?, datetime('now'))",
        (producto_id, cantidad, total)
    )
    cursor.execute(
        "UPDATE productos SET stock = stock - ? WHERE id = ?",
        (cantidad, producto_id)
    )

    conexion.commit()
    conexion.close()

    return jsonify({
        "status": "success",
        "message": "Pago aprobado y venta registrada correctamente",
        "total": total
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)