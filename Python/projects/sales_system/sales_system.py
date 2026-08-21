# SISTEMA DE VENTAS - VERSION 4

producto = input("Ingresa el producto: ")

try:
    precio = float(input("Ingresa el precio: "))
    cantidad = int(input("Ingresa la cantidad: "))

    if precio <= 0:
        raise ValueError("El precio debe ser mayor que 0.")

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