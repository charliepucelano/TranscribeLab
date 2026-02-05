
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/transcribelab")

async def list_jobs():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.get_default_database()
    
    jobs = await db.jobs.find({}, sort=[("created_at", -1)]).to_list(10)
    for job in jobs:
        print(f"ID: {job['_id']} | Name: {job.get('job_name')} | Created: {job.get('created_at')}")

if __name__ == "__main__":
    asyncio.run(list_jobs())
