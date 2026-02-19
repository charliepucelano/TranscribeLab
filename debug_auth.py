
import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.database import db
from app.core.security import verify_password, get_password_hash
from app.core.config import settings

async def debug_user(email: str, password_to_test: str):
    print(f"--- Debugging Auth for {email} ---")
    await db.connect_to_database()
    
    try:
        user = await db.get_db().users.find_one({"email": email})
        if not user:
            print("User not found!")
            return

        print(f"User ID: {user['_id']}")
        print(f"Stored Hash: {user['hashed_password']}")
        
        # Test 1: Verify correctly
        is_valid = verify_password(password_to_test, user['hashed_password'])
        print(f"Testing password '{password_to_test}': {'VALID' if is_valid else 'INVALID'}")
        
        if not is_valid:
            print("Generating new hash for comparison...")
            new_hash = get_password_hash(password_to_test)
            print(f"New Hash (if reset now): {new_hash}")
            
    finally:
        await db.close_database_connection()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python debug_auth.py <email> <password>")
    else:
        asyncio.run(debug_user(sys.argv[1], sys.argv[2]))
