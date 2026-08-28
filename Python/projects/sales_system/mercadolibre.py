import requests

url = "https://api.mercadolibre.com/sites/MPE/categories"

response = requests.get(url)

print("Status:", response.status_code)
print(response.json())