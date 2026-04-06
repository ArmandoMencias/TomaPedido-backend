import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Cargar variables del .env
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Cliente global de MongoDB
client = AsyncIOMotorClient(MONGO_URI)
db = client.Comida_db