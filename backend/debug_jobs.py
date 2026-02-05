import motor.motor_asyncio
import asyncio
from bson import ObjectId

async def check_jobs():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://mongo:27017")
    db = client.transcribelab
    
    print("\n--- Current Jobs Status ---")
    async for job in db.jobs.find().sort("created_at", -1):
        print(f"ID: {job['_id']}")
        print(f" Name: {job.get('job_name', 'Unnamed')}")
        print(f" Status: {job['status']}")
        print(f" Msg: {job.get('status_message', 'No message')}")
        print(f" Progress: {job.get('progress', 0)}%")
        print(f" Has File Key: {job.get('file_key') is not None}")
        print(f" Has File Path: {job.get('file_path') is not None}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(check_jobs())
