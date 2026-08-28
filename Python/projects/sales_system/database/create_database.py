from dotenv import load_dotenv
import os

load_dotenv()

access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")

print("Token encontrado:", access_token is not None)