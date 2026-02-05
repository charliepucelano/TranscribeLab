
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/transcribelab")

async def check_methods_final():
    client = AsyncIOMotorClient(MONGO_URI)
    try:
        db = client.get_default_database()
        print(f"get_default_database: {db.name}")
    except Exception as e:
        print(f"get_default_database FAIL: {e}")
        
    try:
        db = client['transcribelab']
        print(f"Dict access: {db.name}")
    except Exception as e:
        print(f"Dict access FAIL: {e}")

if __name__ == "__main__":
    asyncio.run(check_methods_final())
