# DATA STRUCTURES IN PYTHON


# LISTAS
# Permiten almacenar varios valores y modificarlos.

frutas = ["manzana", "banana", "naranja"]

frutas.append("uva")
frutas.remove("banana")

print(frutas)
print(frutas[0])


# TUPLAS
# Son similares a las listas, pero no se pueden modificar.

coordenadas = (10, 20)

print(coordenadas)
print(coordenadas[0])


# DICCIONARIOS
# Almacenan información mediante pares clave: valor.

persona = {
    "nombre": "Diego",
    "edad": 27,
    "profesion": "Administración"
}

print(persona["nombre"])
print(persona["edad"])

persona["edad"] = 28

print(persona)


# SETS
# Almacenan valores únicos y no mantienen un orden definido.

numeros = {1, 2, 3, 3, 4, 4}

print(numeros)

numeros.add(5)

print(numeros)