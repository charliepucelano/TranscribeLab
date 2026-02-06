from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import settings
from app.core.database import db
from app.models.user import User
from app.core.security import verify_password, get_password_hash

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        # print(f"DEBUG: Token: {token[:10]}...", flush=True)
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            print("DEBUG: Missing 'sub' in token", flush=True)
            raise credentials_exception
    except (JWTError, ValidationError) as e:
        print(f"DEBUG: JWT Validation Failed: {e}", flush=True)
        raise credentials_exception
        
    user = await db.get_db().users.find_one({"email": username})
    if user is None:
        print(f"DEBUG: User not found: {username}", flush=True)
        raise credentials_exception
        
    try:
        if "_id" in user:
            user["_id"] = str(user["_id"])
        
        # Log what we are trying to validate
        # print(f"DEBUG: Validating user: {user.keys()}", flush=True)
        return User(**user)
    except Exception as e:
        print(f"DEBUG: Pydantic Validation Error: {e}", flush=True)
        print(f"DEBUG: User Data Keys: {list(user.keys())}", flush=True)
        raise credentials_exception
