# FUNCTIONS IN PYTHON


# FUNCIÓN BÁSICA

def saludar():
    print("Hola, bienvenido")


saludar()


# PARÁMETROS

def saludar_persona(nombre):
    print(f"Hola, {nombre}")


saludar_persona("Diego")


# VARIOS PARÁMETROS

def sumar(a, b):
    resultado = a + b
    print(resultado)


sumar(10, 5)


# RETURN

def multiplicar(a, b):
    return a * b


resultado = multiplicar(5, 4)

print(resultado)


# VALOR POR DEFECTO

def presentar(nombre, edad=18):
    print(f"Nombre: {nombre}")
    print(f"Edad: {edad}")


presentar("Diego")
presentar("Carlos", 25)


# FUNCIÓN CON CONDICIONAL

def verificar_edad(edad):

    if edad >= 18:
        return "Mayor de edad"

    return "Menor de edad"


resultado = verificar_edad(20)

print(resultado)