
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/transcribelab")

async def check_times():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.get_default_database()
    
    jobs = await db.jobs.find({}, sort=[("created_at", -1)]).to_list(10)
    for job in jobs:
        created_at = job.get('created_at')
        status = job.get('status')
        name = job.get('job_name')
        
        now = datetime.utcnow()
        if created_at:
            delta = now - created_at
            print(f"Job: {name} | Status: {status}")
            print(f" - Created: {created_at} (UTC)")
            print(f" - Running Time: {delta}")
        else:
            print(f"Job: {name} | Status: {status} | No created_at")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(check_times())
