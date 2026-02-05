from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from app.services.security import decrypt_data, decode_str
import json
import os
import traceback

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

    file_key = decode_str(j['file_key'])
    
    try:
        with open(path, "rb") as f:
            encrypted = f.read()
            
        print(f"Encrypted size: {len(encrypted)}")
        decrypted = decrypt_data(encrypted, file_key)
        print(f"Decrypted size: {len(decrypted)}")
        
        data = json.loads(decrypted.decode('utf-8'))
        print("JSON Parse: SUCCESS")
        print(f"Num Segments: {len(data)}")
        if len(data) > 0:
            print(f"Sample: {data[0]}")
            
    except Exception as e:
        print("TRANSCRIPT DECRYPTION FAILED:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug())
