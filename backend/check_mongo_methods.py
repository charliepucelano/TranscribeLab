
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/transcribelab")

async def check_client():
    client = AsyncIOMotorClient(MONGO_URI)
    print(f"Client: {type(client)}")
    print(f"Dir: {dir(client)}")
    try:
        db = client.get_database()
        print(f"get_database() OK: {db.name}")
    except AttributeError:
        print("get_database() MISSING")
        
    try:
        db = client.get_default_database()
        print(f"get_default_database() OK: {db.name}")
    except AttributeError:
        print("get_default_database() MISSING")

if __name__ == "__main__":
    asyncio.run(check_client())
