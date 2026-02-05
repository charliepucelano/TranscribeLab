
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Direct connection using env var or fallback
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/transcribelab")

async def check():
    print("--- STARTING CHECK ---")
    print(f"URI: {MONGO_URI}")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.transcribelab
    users = db.users
    
    print("Searching for caleyur@gmail.com...")
    user = await users.find_one({"email": "caleyur@gmail.com"})
    
    if user:
        print("!!! USER FOUND !!!")
        print(f"ID: {user['_id']}")
        print(f"Email: {user['email']}")
    else:
        print("XXX USER NOT FOUND XXX")
        
    print("--- END CHECK ---")

if __name__ == "__main__":
    asyncio.run(check())
