import asyncio
from app.core.database import db
from app.core.crypto import decode_str, decrypt_data
import os
import json

async def check():
    db.connect()
    # Find most recent job
    job = await db.get_db().jobs.find_one(sort=[("created_at", -1)])
    if not job:
        print("No jobs found")
        return

    print(f"Checking Job ID: {job['_id']}")
    
    enc_key = job.get('file_key')
    t_path = job.get('transcript_path')
    
    if not enc_key:
        print("FAIL: No file_key in DB")
        return
        
    if not t_path or not os.path.exists(t_path):
        print("FAIL: No transcript file")
        return
        
    try:
        key = decode_str(enc_key)
        print("Key decoded successfully.")
        
        with open(t_path, "rb") as f:
            content = f.read()
            
        print(f"Read {len(content)} bytes from file.")
        
        decrypted = decrypt_data(content, key)
        print("Decrypted successfully.")
        
        data = json.loads(decrypted.decode('utf-8'))
        print("JSON parsed successfully.")
        print(f"Segment Count: {len(data.get('segments', []))}")
        
    except Exception as e:
        print("--------------------------------------------------")
        print(f"CRITICAL FAILURE: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        print("--------------------------------------------------")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check())
