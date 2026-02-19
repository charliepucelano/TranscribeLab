
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/backend")

from app.core.database import db

async def make_admin(email: str):
    db.connect()
    try:
        user = await db.get_db().users.find_one({"email": email})
        if not user:
            print(f"User {email} not found.")
            return

        await db.get_db().users.update_one(
            {"email": email},
            {"$set": {"is_superuser": True}}
        )
        print(f"User {email} is now an admin (superuser).")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/make_admin.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    asyncio.run(make_admin(email))
