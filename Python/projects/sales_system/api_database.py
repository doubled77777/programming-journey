import requests
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "sales.db"


url = "https://jsonplaceholder.typicode.com/posts"

respuesta = requests.get(url)

print("Código:", respuesta.status_code)

datos = respuesta.json()


conexion = sqlite3.connect(DB_PATH)
print("Base de datos usada:", DB_PATH)
cursor = conexion.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS posts_api (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER,
    titulo TEXT NOT NULL
)
""")


for dato in datos[:5]:

    cursor.execute("""
        INSERT OR IGNORE INTO posts_api
        (id, usuario_id, titulo)
        VALUES (?, ?, ?)
    """, (
        dato["id"],
        dato["userId"],
        dato["title"]
    ))


conexion.commit()


cursor.execute("SELECT * FROM posts_api")

cursor.execute("""
    SELECT titulo
    FROM posts_api
    WHERE usuario_id = ?
""", (1,))

titulos = cursor.fetchall()

print("\n--- POSTS DEL USUARIO 1 ---")

for titulo in titulos:
    print(titulo[0])

posts = cursor.fetchall()

print("\nTablas de la base de datos:")

cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
""")

tablas = cursor.fetchall()

print(tablas)

print("\n--- DATOS GUARDADOS ---")

for post in posts:
    print(post)

import csv
cursor.execute("""
    SELECT id, usuario_id, titulo
    FROM posts_api
""")

posts = cursor.fetchall()
REPORT_PATH = BASE_DIR / "reporte_api.csv"

with open(REPORT_PATH, "w", newline="", encoding="utf-8") as archivo:
    escritor = csv.writer(archivo)

    escritor.writerow([
        "ID",
        "Usuario",
        "Título"
    ])

    for post in posts:
        escritor.writerow(post)

print("\nReporte generado correctamente.")
print(f"Archivo: {REPORT_PATH}")


conexion.close()