
try:
    from passlib.context import CryptContext
    
    # Replicate configuration from app/core/security.py
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    
    password = "password123"
    hashed = pwd_context.hash(password)
    print(f"Password: {password}")
    print(f"Hashed: {hashed}")
    
    is_valid = pwd_context.verify(password, hashed)
    print(f"Verify match: {is_valid}")
    
    is_invalid = pwd_context.verify("wrongpassword", hashed)
    print(f"Verify mismatch: {is_invalid}")
    
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
