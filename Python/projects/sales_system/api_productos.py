import requests
import sqlite3
from pathlib import Path


url = "https://dummyjson.com/products"

respuesta = requests.get(url)

print("Código:", respuesta.status_code)

datos = respuesta.json()

productos = datos["products"]


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "sales.db"


conexion = sqlite3.connect(DB_PATH)
cursor = conexion.cursor()


print("\n--- PRODUCTOS DE LA API ---")


for producto in productos[:5]:

    cursor.execute(
        "SELECT id FROM productos WHERE nombre = ?",
        (producto["title"],)
    )

    producto_existente = cursor.fetchone()

    if producto_existente:

        print(f"Ya existe: {producto['title']}")

    else:

        cursor.execute("""
            INSERT INTO productos (nombre, precio, stock)
            VALUES (?, ?, ?)
        """, (
            producto["title"],
            producto["price"],
            10
        ))

        print(f"Importado: {producto['title']}")


conexion.commit()
conexion.close()


print("\nProceso de importación terminado.")