
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from app.models.job import Job

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/transcribelab")

async def test_real_data():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.transcribelab
    
    print("Fetching last job...")
    job_doc = await db.jobs.find_one({}, sort=[("created_at", -1)])
    
    if not job_doc:
        print("No jobs found in DB.")
        return

    print(f"Raw DB Doc: {job_doc}")
    
    try:
        print("Attempting validation...")
        job = Job(**job_doc)
        print("Validation SUCCESS!")
        print(f"Dump: {job.model_dump()}")
        print(f"JSON: {job.model_dump_json()}")
    except Exception as e:
        print(f"Validation FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_data())
