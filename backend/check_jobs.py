
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import pprint

# Direct connection using env var or fallback
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/transcribelab")

async def check_jobs():
    print("--- STARTING JOB CHECK ---")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.transcribelab
    
    # 1. Find User
    print("Finding user cleyurzaiz@gmail.com...")
    user = await db.users.find_one({"email": "cleyurzaiz@gmail.com"})
    if not user:
        print("XXX User not found with exact email 'caleyur@gmail.com'")
        print("--- LISTING ALL USERS ---")
        async for u in db.users.find():
            print(f"User: {u.get('email')} | ID: {u.get('_id')}")
        return

    user_id = str(user["_id"])
    print(f"User ID: {user_id}")
    
    # 2. Find Jobs
    print(f"Searching for jobs for user_id: {user_id}")
    jobs_cursor = db.jobs.find({"user_id": user_id})
    jobs = await jobs_cursor.to_list(100)
    
    print(f"Found {len(jobs)} jobs.")
    for job in jobs:
        print(f" - Job: {job.get('job_name')} | Status: {job.get('status')} | ID: {job['_id']}")
        
    print("--- ALL JOBS DUMP ---")
    all_jobs = await db.jobs.find({}).to_list(10)
    for job in all_jobs:
        print(f" [ALL] Job: {job.get('job_name')} | UserID: {job.get('user_id')} | Status: {job.get('status')}")

if __name__ == "__main__":
    asyncio.run(check_jobs())
