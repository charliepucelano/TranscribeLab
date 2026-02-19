
import asyncio
import os
import sys

# Add /app to sys.path to ensure we can import app modules if running from /app root
sys.path.append('/app')

from app.core.database import db
from app.core.security import verify_password, get_password_hash
from app.core.config import settings

async def debug_user(email: str, password_to_test: str):
    print(f"--- Debugging Auth for {email} ---")
    
    # Check Mongo URI debug
    print(f"Connecting to: {settings.MONGO_URI}", flush=True)
    
    db.connect()
    
    try:
        print(f"Searching for user {email}...", flush=True)
        user = await db.get_db().users.find_one({"email": email})
        
        if not user:
            print("User not found!", flush=True)
            print("Listing all users:", flush=True)
            async for u in db.get_db().users.find():
                print(f"- {u.get('email')}", flush=True)
            return

        print(f"User found: {user.get('_id')}", flush=True)
        # Use .get() to avoid KeyError if field is missing
        stored_hash = user.get('hashed_password')
        print(f"Stored Hash type: {type(stored_hash)}", flush=True)
        print(f"Stored Hash: {repr(stored_hash)}", flush=True)
        
        if not stored_hash:
            print("ERROR: User has no hashed_password!", flush=True)
        
        # Check is_active
        print(f"Is Active: {user.get('is_active')}", flush=True)
        
        # Test 1: Verify correctly
        try:
            print(f"Verifying password '{password_to_test}'...", flush=True)
            is_valid = verify_password(password_to_test, stored_hash)
            print(f"Result: {'VALID' if is_valid else 'INVALID'}", flush=True)
            
            if is_valid:
                # Test Token Gen
                print("Attempting to generate access token...", flush=True)
                from app.core.security import create_access_token
                from datetime import timedelta
                
                access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                token = create_access_token(
                    data={"sub": user["email"]}, expires_delta=access_token_expires
                )
                print(f"Token generated successfully: {token[:20]}...", flush=True)

        except Exception as e:
            print(f"Error verifying password/token: {e}", flush=True)
            import traceback
            traceback.print_exc()
        
        # Test 2: Generate new hash
        new_hash = get_password_hash(password_to_test)
        print(f"New Hash (if reset now): {new_hash}", flush=True)
            
    except Exception as e:
        print(f"An error occurred: {e}", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python debug_auth.py <email> <password>")
    else:
        asyncio.run(debug_user(sys.argv[1], sys.argv[2]))
