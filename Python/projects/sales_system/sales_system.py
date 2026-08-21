# SISTEMA DE VENTAS - VERSION 6

productos = {
    "laptop": 2500,
    "mouse": 80,
    "teclado": 150
}

carrito = []

print("--- PRODUCTOS DISPONIBLES ---")

for producto, precio in productos.items():
    print(producto, "-", precio)

while True:

    producto = input("\nIngresa un producto (o 'salir'): ").lower()

    if producto == "salir":
        break

    if producto not in productos:
        print("El producto no existe.")
        continue

    try:
        cantidad = int(input("Ingresa la cantidad: "))

        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0.")

    except ValueError as error:
        print("Error:", error)
        continue

    precio = productos[producto]
    subtotal = precio * cantidad

    carrito.append({
        "producto": producto,
        "precio": precio,
        "cantidad": cantidad,
        "subtotal": subtotal
    })

    print("Producto agregado al carrito.")


print("\n--- RESUMEN DE COMPRA ---")

total = 0

for venta in carrito:
    print(
        venta["producto"],
        "- Cantidad:",
        venta["cantidad"],
        "- Subtotal:",
        venta["subtotal"]
    )

    total += venta["subtotal"]

print("\nTOTAL:", total)