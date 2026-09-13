import sqlite3
from pathlib import Path
from flask import Flask, request, jsonify

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "sales.db"


def get_db_connection():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row  # permite acceder a columnas por nombre
    return conexion


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

    if producto_id is None or cantidad is None:
        return jsonify({
            "status": "error",
            "message": "Faltan datos: se requiere producto_id y cantidad"
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
        "message": "Venta registrada correctamente",
        "total": total
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)