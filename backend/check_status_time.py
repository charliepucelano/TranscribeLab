from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
import datetime

async def check():
    client = AsyncIOMotorClient('mongodb://mongo:27017')
    db = client.transcribelab
    j = await db.jobs.find_one(sort=[('created_at', -1)])
    
    if not j:
        print("No job found")
        return
        
    print(f"DB Status: {j.get('status')}")
    print(f"Msg: {j.get('status_message')}")
    print(f"Progress: {j.get('progress')}")
    
    path = j.get('transcript_path')
    if path and os.path.exists(path):
        mtime = os.path.getmtime(path)
        dt = datetime.datetime.fromtimestamp(mtime)
        size = os.path.getsize(path)
        print(f"Transcript Path: {path}")
        print(f"Transcript Last Modified: {dt}")
        print(f"Transcript Size: {size} bytes")
    else:
        print("Transcript file not found")

if __name__ == "__main__":
    asyncio.run(check())
