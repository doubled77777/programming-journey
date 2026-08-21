# CONTROL DE FLUJO EN PYTHON

# IF / ELIF / ELSE

edad = 20

if edad >= 18:
    print("Mayor de edad")
elif edad >= 13:
    print("Adolescente")
else:
    print("Menor de edad")


# FOR

for numero in range(5):
    print(numero)


# WHILE

contador = 0

while contador < 5:
    print(contador)
    contador += 1


# BREAK

for numero in range(10):
    if numero == 5:
        break

    print(numero)


# CONTINUE

for numero in range(5):
    if numero == 2:
        continue

    print(numero)