import sqlite3
from pathlib import Path


# Buscar la base de datos correctamente
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "sales.db"

conexion = sqlite3.connect(DB_PATH)
cursor = conexion.cursor()

carrito = []


def mostrar_productos():
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()

    print("\n--- PRODUCTOS ---")

    for producto in productos:
        print(
            f"{producto[0]}. "
            f"{producto[1]} - "
            f"S/ {producto[2]} - "
            f"Stock: {producto[3]}"
        )


def agregar_producto():
    nombre = input("Nombre del producto: ")
    precio = float(input("Precio: "))
    stock = int(input("Stock inicial: "))

    cursor.execute(
        """
        INSERT INTO productos (nombre, precio, stock)
        VALUES (?, ?, ?)
        """,
        (nombre, precio, stock)
    )

    conexion.commit()

    print("Producto agregado correctamente.")


def agregar_al_carrito():
    mostrar_productos()

    producto_id = int(input("\nID del producto: "))
    cantidad = int(input("Cantidad: "))

    cursor.execute(
        "SELECT * FROM productos WHERE id = ?",
        (producto_id,)
    )

    producto = cursor.fetchone()

    if producto is None:
        print("Producto no encontrado.")
        return

    if cantidad <= 0:
        print("La cantidad debe ser mayor que 0.")
        return

    if cantidad > producto[3]:
        print("No hay suficiente stock.")
        return

    carrito.append({
        "id": producto[0],
        "nombre": producto[1],
        "precio": producto[2],
        "cantidad": cantidad
    })

    print("Producto agregado al carrito.")


def mostrar_carrito():
    if not carrito:
        print("\nEl carrito está vacío.")
        return

    total = 0

    print("\n--- CARRITO ---")

    for producto in carrito:
        subtotal = producto["precio"] * producto["cantidad"]

        print(
            f"{producto['nombre']} x "
            f"{producto['cantidad']} = "
            f"S/ {subtotal}"
        )

        total += subtotal

    print(f"\nTOTAL: S/ {total}")


def finalizar_compra():
    if not carrito:
        print("\nEl carrito está vacío.")
        return

    total = 0

    for producto in carrito:
        subtotal = producto["precio"] * producto["cantidad"]

        total += subtotal

        # Guardar venta
        cursor.execute(
            """
            INSERT INTO ventas
            (producto_id, cantidad, total, fecha)
            VALUES (?, ?, ?, datetime('now'))
            """,
            (
                producto["id"],
                producto["cantidad"],
                subtotal
            )
        )

        # Reducir stock
        cursor.execute(
            """
            UPDATE productos
            SET stock = stock - ?
            WHERE id = ?
            """,
            (
                producto["cantidad"],
                producto["id"]
            )
        )

    conexion.commit()

    print("\nCompra realizada correctamente.")
    print(f"Total pagado: S/ {total}")

    carrito.clear()


while True:

    print("\n=== SISTEMA DE VENTAS ===")
    print("1. Ver productos")
    print("2. Agregar producto")
    print("3. Agregar al carrito")
    print("4. Ver carrito")
    print("5. Finalizar compra")
    print("6. Salir")

    opcion = input("Selecciona una opción: ")

    if opcion == "1":
        mostrar_productos()

    elif opcion == "2":
        agregar_producto()

    elif opcion == "3":
        agregar_al_carrito()

    elif opcion == "4":
        mostrar_carrito()

    elif opcion == "5":
        finalizar_compra()

    elif opcion == "6":
        break

    else:
        print("Opción inválida.")


conexion.close()