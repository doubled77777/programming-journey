import sqlite3
from pathlib import Path


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

    cursor.execute(
        "SELECT * FROM productos WHERE LOWER(nombre) = LOWER(?)",
        (nombre,)
    )

    producto = cursor.fetchone()

    if producto:
        print(f"\nEl producto '{producto[1]}' ya existe.")
        print(f"Precio actual: S/ {producto[2]}")
        print(f"Stock actual: {producto[3]}")

        respuesta = input("¿Deseas aumentar el stock? (s/n): ").lower()

        if respuesta == "s":
            cantidad = int(input("Cantidad a agregar: "))

            if cantidad <= 0:
                print("La cantidad debe ser mayor que 0.")
                return

            cursor.execute(
                """
                UPDATE productos
                SET stock = stock + ?
                WHERE id = ?
                """,
                (cantidad, producto[0])
            )

            conexion.commit()

            print("Stock actualizado correctamente.")

        else:
            print("No se realizó ningún cambio.")

        return

    precio = float(input("Precio: "))
    stock = int(input("Stock inicial: "))

    if precio < 0 or stock < 0:
        print("El precio y el stock no pueden ser negativos.")
        return

    print("\n--- NUEVO PRODUCTO ---")
    print(f"Nombre: {nombre}")
    print(f"Precio: S/ {precio}")
    print(f"Stock: {stock}")

    confirmar = input("¿Confirmar producto? (s/n): ").lower()

    if confirmar != "s":
        print("Producto cancelado.")
        return

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


def historial_ventas():
    cursor.execute("""
        SELECT
            ventas.id,
            productos.nombre,
            ventas.cantidad,
            ventas.total,
            ventas.fecha
        FROM ventas
        INNER JOIN productos
            ON ventas.producto_id = productos.id
        ORDER BY ventas.id DESC
    """)

    ventas = cursor.fetchall()

    if not ventas:
        print("\nNo hay ventas registradas.")
        return

    print("\n--- HISTORIAL DE VENTAS ---")

    for venta in ventas:
        print(
            f"Venta #{venta[0]} | "
            f"{venta[1]} | "
            f"Cantidad: {venta[2]} | "
            f"Total: S/ {venta[3]} | "
            f"Fecha: {venta[4]}"
        )


while True:

    print("\n=== SISTEMA DE VENTAS ===")
    print("1. Ver productos")
    print("2. Agregar producto")
    print("3. Agregar al carrito")
    print("4. Ver carrito")
    print("5. Finalizar compra")
    print("6. Salir")
    print("7. Ver historial de ventas")

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

    elif opcion == "7":
        historial_ventas()

    else:
        print("Opción inválida.")


conexion.close()