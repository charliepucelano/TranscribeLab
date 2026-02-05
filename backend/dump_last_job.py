import motor.motor_asyncio
import asyncio
from bson import ObjectId

async def dump_last_job():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://mongo:27017")
    db = client.transcribelab
    job = await db.jobs.find_one(sort=[("created_at", -1)])
    if job:
        print(f"ID: {job['_id']}")
        print(f"Status: {job['status']}")
        print(f"Message: {job.get('status_message')}")
        print(f"Original Filename: {job.get('original_filename')}")
        print(f"Filename: {job.get('filename')}")
        print(f"Progress: {job.get('progress')}")
        print(f"File Path: {job.get('file_path')}")
        print(f"Has File Key: {job.get('file_key') is not None}")
    else:
        print("No jobs found")

if __name__ == "__main__":
    asyncio.run(dump_last_job())
