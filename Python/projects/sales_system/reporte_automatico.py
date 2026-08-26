import sqlite3
import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "sales.db"
REPORT_PATH = BASE_DIR / "reporte_ventas.csv"


conexion = sqlite3.connect(DB_PATH)
cursor = conexion.cursor()


cursor.execute("""
    SELECT
        productos.nombre,
        SUM(ventas.cantidad) AS unidades_vendidas,
        SUM(ventas.total) AS ingresos
    FROM ventas
    INNER JOIN productos
        ON ventas.producto_id = productos.id
    GROUP BY productos.id
    ORDER BY ingresos DESC
""")


ventas = cursor.fetchall()


with open(REPORT_PATH, "w", newline="", encoding="utf-8") as archivo:

    escritor = csv.writer(archivo)

    escritor.writerow([
        "Producto",
        "Unidades vendidas",
        "Ingresos"
    ])

    for venta in ventas:
        escritor.writerow(venta)


conexion.close()

print("Reporte generado correctamente.")
print(f"Archivo: {REPORT_PATH}")