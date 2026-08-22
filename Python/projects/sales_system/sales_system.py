# SISTEMA DE VENTAS - VERSION 8

productos = {
    "laptop": 2500,
    "mouse": 80,
    "teclado": 150
}

carrito = []


def mostrar_productos():
    print("--- PRODUCTOS DISPONIBLES ---")

    for producto, precio in productos.items():
        print(producto, "-", precio)


def agregar_al_carrito():
    producto = input("\nIngresa un producto (o 'salir'): ").lower()

    if producto == "salir":
        return False

    if producto not in productos:
        print("El producto no existe.")
        return True

    try:
        cantidad = int(input("Ingresa la cantidad: "))

        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0.")

    except ValueError as error:
        print("Error:", error)
        return True

    precio = productos[producto]
    subtotal = precio * cantidad

    carrito.append({
        "producto": producto,
        "precio": precio,
        "cantidad": cantidad,
        "subtotal": subtotal
    })

    print("Producto agregado al carrito.")

    return True


def mostrar_carrito():
    print("\n--- RESUMEN DE COMPRA ---")

    for venta in carrito:
        print(
            venta["producto"],
            "- Cantidad:",
            venta["cantidad"],
            "- Subtotal:",
            venta["subtotal"]
        )


def calcular_total():
    total = 0

    for venta in carrito:
        total += venta["subtotal"]

    return total


def calcular_descuento(total):

    if total < 500:
        return 0

    elif total < 1000:
        return 5

    elif total < 2000:
        return 10

    else:
        return 15


mostrar_productos()

while True:

    continuar = agregar_al_carrito()

    if not continuar:
        break


mostrar_carrito()

total = calcular_total()

descuento = calcular_descuento(total)

monto_descuento = total * descuento / 100

total_final = total - monto_descuento

print("\n--- TOTAL DE LA COMPRA ---")
print("Subtotal:", total)
print("Descuento:", descuento, "%")
print("Ahorro:", monto_descuento)
print("TOTAL FINAL:", total_final)