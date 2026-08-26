import requests

url = "https://jsonplaceholder.typicode.com/posts"

respuesta = requests.get(url)

print("Código:", respuesta.status_code)

datos = respuesta.json()

for dato in datos[:5]:
    print(dato["title"])