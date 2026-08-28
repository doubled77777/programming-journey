from dotenv import load_dotenv
import os
import requests
import uuid

load_dotenv()

access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "X-Idempotency-Key": str(uuid.uuid4())
}

order = {
    "type": "online",
    "processing_mode": "manual",
    "total_amount": "10.00",
    "external_reference": "sales-system-test-001",
    "payer": {
    "email": "comprador@testuser.com"
},
    "items": [
    {
        "title": "Producto de prueba",
        "unit_price": "10.00",
        "quantity": 1
    }
]
}

response = requests.post(
    "https://api.mercadopago.com/v1/orders",
    headers=headers,
    json=order
)

print("Status:", response.status_code)
print(response.json())