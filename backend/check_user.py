
import asyncio
from app.core.database import db
from app.core.config import settings

async def check():
    print(f"Connecting to {settings.MONGO_URI}")
    db.connect()
    user = await db.get_db().users.find_one({"email": "caleyur@gmail.com"})
    if user:
        print("User found!")
        print(f"Email: {user['email']}")
        print(f"Is Active: {user['is_active']}")
    else:
        print("User NOT found.")
    db.close()

if __name__ == "__main__":
    asyncio.run(check())
