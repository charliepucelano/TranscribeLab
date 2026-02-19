from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from app.core.database import db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.api.dependencies import get_current_user, oauth2_scheme
from app.models.user import UserCreate, UserInDB, User, UserRegistered
from app.core.config import settings
from bson import ObjectId

router = APIRouter()


from app.core.crypto import generate_salt, generate_key, derive_key, encrypt_data, encode_bytes, decode_str

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
    
    # Calculate Master Key Hash (SHA256) for verification during recovery
    import hashlib
    master_key_hash = hashlib.sha256(master_key).hexdigest()

    # Create user
    user = UserInDB(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        encrypted_master_key=encode_bytes(encrypted_master_key),
        master_key_hash=master_key_hash,
        key_derivation_salt=encode_bytes(salt),
        is_active=True
    )
    
    new_user = await db.get_db().users.insert_one(user.model_dump(by_alias=True, exclude={"id"}))
    created_user = await db.get_db().users.find_one({"_id": new_user.inserted_id})
    
    # Return user with Recovery Key (only time it's exposed)
    return UserRegistered(**created_user, recovery_key=encode_bytes(master_key))

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    recovery_key: str
    new_password: str

@router.post("/reset-password", response_model=User)
async def reset_password(reset_in: ResetPasswordRequest):
    user = await db.get_db().users.find_one({"email": reset_in.email})
    if not user:
        # Avoid user enumeration (fake delay could be added here)
        raise HTTPException(status_code=400, detail="Invalid request")

    # Verify Recovery Key
    try:
        recovery_key_bytes = decode_str(reset_in.recovery_key)
    except:
         raise HTTPException(status_code=400, detail="Invalid recovery key format")

    import hashlib
    calculated_hash = hashlib.sha256(recovery_key_bytes).hexdigest()
    
    if calculated_hash != user.get("master_key_hash"):
         raise HTTPException(status_code=400, detail="Invalid recovery key")
    
    # Key is valid. Re-encrypt vault with new password.
    # 1. Generate new salt
    new_salt = generate_salt()
    
    # 2. Derive new KEK
    new_kek = derive_key(reset_in.new_password, new_salt)
    
    # 3. Encrypt Master Key (Recovery Key) with new KEK
    new_encrypted_master_key = encrypt_data(recovery_key_bytes, new_kek)
    
    # Update DB
    await db.get_db().users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "hashed_password": get_password_hash(reset_in.new_password),
                "encrypted_master_key": encode_bytes(new_encrypted_master_key),
                "key_derivation_salt": encode_bytes(new_salt)
            }
        }
    )
    
    updated_user = await db.get_db().users.find_one({"_id": user["_id"]})
    return User(**updated_user)


@router.post("/invite")
async def create_invitation(current_user: User = Depends(get_current_user)):
    # Create a signed token with "invite" scope
    # For now, just a long-lived JWT or similar. 
    # To keep it simple, we'll just return a link to register page with a cosmetic parameter
    # In a real system, /register would validate this token.
    # We will implement /register validation in the next step if requested.
    
    # Here we just generate a simple client-side link for now as per plan
    import secrets
    token = secrets.token_urlsafe(16)
    link = f"http://{settings.DOMAIN_NAME or 'localhost:3000'}/register?invite={token}"
    
    return {"invitation_link": link, "note": "Share this link. (Token validation pending in next iteration)"}


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


class ChangePasswordRequest(BaseModel):
    new_password: str

@router.post("/update-password")
async def update_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user)
):
    # Update password and clear force flag
    await db.get_db().users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {
            "hashed_password": get_password_hash(request.new_password),
            "force_password_change": False
        }}
    )
    return {"message": "Password updated successfully"}

class RecoveryKeyRequest(BaseModel):
    password: str

@router.post("/recovery-key")
async def get_recovery_key(
    request: RecoveryKeyRequest,
    current_user: User = Depends(get_current_user)
):
    # 1. Verify password
    user_in_db = await db.get_db().users.find_one({"_id": ObjectId(current_user.id)})
    if not verify_password(request.password, user_in_db["hashed_password"]):
         raise HTTPException(status_code=400, detail="Incorrect password")

    # 2. Derive KEK
    try:
        salt = decode_str(user_in_db["key_derivation_salt"])
        kek = derive_key(request.password, salt)
        
        # 3. Decrypt Master Key
        encrypted_master_key = decode_str(user_in_db["encrypted_master_key"])
        from app.core.crypto import decrypt_data
        master_key = decrypt_data(encrypted_master_key, kek)
        
        # 4. Return as hex/string
        return {"recovery_key": encode_bytes(master_key)}
    except Exception as e:
        print(f"Error retrieving recovery key: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recovery key")

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

