from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from app.core.database import db
from app.core.auth import get_password_hash, verify_password, create_access_token
from app.models.user import UserCreate, UserInDB, User
from app.core.config import settings
from bson import ObjectId

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        from jose import jwt, JWTError
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = await db.get_db().users.find_one({"email": email})
    if user is None:
        raise credentials_exception
    return User(**user)

from app.core.crypto import generate_salt, generate_key, derive_key, encrypt_data, encode_bytes

@router.post("/register", response_model=User)
async def register(user_in: UserCreate):
    # Check if user exists
    existing_user = await db.get_db().users.find_one({"email": user_in.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate Encryption Keys
    # 1. Generate a random Master Key for this user
    master_key = generate_key()
    
    # 2. Generate a salt for KEK derivation
    salt = generate_salt()
    
    # 3. Derive Key-Encryption-Key (KEK) from user password
    kek = derive_key(user_in.password, salt)
    
    # 4. Encrypt the Master Key with the KEK
    encrypted_master_key = encrypt_data(master_key, kek)
    
    # Create user
    user = UserInDB(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        encrypted_master_key=encode_bytes(encrypted_master_key),
        key_derivation_salt=encode_bytes(salt),
        is_active=True
    )
    
    new_user = await db.get_db().users.insert_one(user.model_dump(by_alias=True, exclude={"id"}))
    created_user = await db.get_db().users.find_one({"_id": new_user.inserted_id})
    
    return User(**created_user)

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.get_db().users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
