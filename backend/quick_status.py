
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/transcribelab")

async def status():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.get_default_database()
    job = await db.jobs.find_one({}, sort=[("created_at", -1)])
    if job:
        print(f"JOB STATUS: {job.get('status')}")
    else:
        print("JOB NOT FOUND")

if __name__ == "__main__":
    asyncio.run(status())
