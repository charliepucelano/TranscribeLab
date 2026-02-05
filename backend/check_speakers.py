from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from app.core.crypto import decode_str, decrypt_data
import json

async def check():
    client = AsyncIOMotorClient('mongodb://mongo:27017')
    db = client.transcribelab
    j = await db.jobs.find_one(sort=[('created_at', -1)])
    if not j:
        print("No job found")
        return

    try:
        key = decode_str(j['file_key'])
        path = j['transcript_path']
        with open(path, 'rb') as f:
            enc = f.read()
            dec = decrypt_data(enc, key)
            data = json.loads(dec)
            
        speakers = set()
        for s in data['segments']:
            speakers.add(s.get('speaker', 'None'))
            
        print(f"Speakers found: {speakers}")
    except Exception as e:
        print(f"Error checking speakers: {e}")

if __name__ == "__main__":
    asyncio.run(check())
