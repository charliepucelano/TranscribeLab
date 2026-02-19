
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from app.core.security import get_password_hash, verify_password
    
    password = "password123"
    hashed = get_password_hash(password)
    print(f"Password: {password}")
    print(f"Hashed: {hashed}")
    
    is_valid = verify_password(password, hashed)
    print(f"Verify match: {is_valid}")
    
    is_invalid = verify_password("wrongpassword", hashed)
    print(f"Verify mismatch: {is_invalid}")
    
except Exception as e:
    print(f"Error: {e}")
