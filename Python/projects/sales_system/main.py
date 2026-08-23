import sqlite3


conexion = sqlite3.connect(
    "Python/projects/sales_system/database/sales.db"
)

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