# SISTEMA DE VENTAS - VERSION 5

productos = {
    "laptop": 2500,
    "mouse": 80,
    "teclado": 150
}

print("--- PRODUCTOS DISPONIBLES ---")

for producto, precio in productos.items():
    print(producto, "-", precio)


producto = input("\nIngresa el producto: ").lower()

if producto in productos:

    precio = productos[producto]

    try:
        cantidad = int(input("Ingresa la cantidad: "))

        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0.")

    except ValueError as error:
        print("Error:", error)

    else:
        subtotal = precio * cantidad

        print("\n--- RESUMEN DE COMPRA ---")
        print("Producto:", producto)
        print("Precio:", precio)
        print("Cantidad:", cantidad)
        print("Subtotal:", subtotal)

else:
    print("El producto no existe.")