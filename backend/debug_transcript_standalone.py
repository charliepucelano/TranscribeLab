from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from cryptography.fernet import Fernet
import json
import os
import base64

def decode_str(s):
    if not s: return None
    return base64.b64decode(s.encode('utf-8')) if isinstance(s, str) else s

def decrypt_data(encrypted_data, key):
    f = Fernet(key)
    return f.decrypt(encrypted_data)

async def debug():
    client = AsyncIOMotorClient('mongodb://mongo:27017')
    db = client.transcribelab
    j = await db.jobs.find_one(sort=[('created_at', -1)])
    
    if not j:
        print("No job found")
        return

    print(f"Checking Transcript for Job: {j.get('_id')}")
    path = j.get('transcript_path')
    
    if not path or not os.path.exists(path):
        print(f"Path missing: {path}")
        return

    file_key_enc = j.get('file_key')
    # It might be stored as string in DB?
    # In job.py: file_key: Optional[str]
    # In encryption, it usually is bytes. Checking how it is stored.
    # Usually we store the key itself.
    
    # If the key in DB is already bytes, good. If string, encode?
    # Fernet key must be 32 url-safe base64-encoded bytes.
    # Let's try raw first.
    
    # In app/services/security.py, usually we handle this.
    # Assuming standard Fernet usage.
    
    try:
        # file_key in DB is likely the Fernet Key itself or encrypted key?
        # Looking at previous code view: file_key = decode_str(job["file_key"])
        # So it is base64 encoded string.
        
        # job['file_key'] is the field.
        # job['file_key'] is the field.
        # It should be the base64 key string itself.
        raw_key_str = file_key_enc
        
        print(f"Key from DB: {raw_key_str}")
        
        if isinstance(raw_key_str, str):
             real_key = raw_key_str.encode('utf-8')
        else:
             real_key = raw_key_str
             
        # Test validation
        Fernet(real_key) 
        
        # Ensure it is bytes for Fernet
        if isinstance(real_key, str):
             real_key = real_key.encode('utf-8')
        
        # Test if it is valid by making a dummy Fernet
        try:
            Fernet(real_key)
            print("Fernet Init: OK")
        except Exception as e:
            print(f"Fernet Init Failed: {e}")
            return
        
        with open(path, "rb") as f:
            encrypted = f.read()
            
        print(f"Encrypted size: {len(encrypted)}")
        decrypted = decrypt_data(encrypted, real_key)
        print(f"Decrypted size: {len(decrypted)}")
        
        data = json.loads(decrypted.decode('utf-8'))
        print("JSON Parse: SUCCESS")
        print(f"Num Segments: {len(data)}")
        if isinstance(data, list):
            print(f"Sample: {data[:2]}") # Print first 2
        else:
            print(f"Data type: {type(data)}")
            print(f"Content: {data}")
            
    except Exception as e:
        with open("debug_error.log", "w") as log:
            import traceback
            traceback.print_exc(file=log)
        print("TRANSCRIPT DECRYPTION FAILED: Check debug_error.log")

if __name__ == "__main__":
    asyncio.run(debug())
