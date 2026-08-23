import sqlite3


conexion = sqlite3.connect(
    "Python/projects/sales_system/database/sales.db"
)

cursor = conexion.cursor()


def mostrar_productos():
    cursor.execute("SELECT * FROM productos")

    productos = cursor.fetchall()

    print("\n--- PRODUCTOS ---")

    for producto in productos:
        print(
            f"{producto[0]}. "
            f"{producto[1]} - "
            f"S/ {producto[2]}"
        )


def agregar_producto():
    nombre = input("Nombre del producto: ")
    precio = float(input("Precio: "))

    cursor.execute(
        """
        INSERT INTO productos (nombre, precio)
        VALUES (?, ?)
        """,
        (nombre, precio)
    )

    conexion.commit()

    print("Producto agregado correctamente.")


while True:

    print("\n=== SISTEMA DE VENTAS ===")
    print("1. Ver productos")
    print("2. Agregar producto")
    print("3. Salir")

    opcion = input("Selecciona una opción: ")

    if opcion == "1":
        mostrar_productos()

    elif opcion == "2":
        agregar_producto()

    elif opcion == "3":
        break

    else:
        print("Opción inválida.")


conexion.close()