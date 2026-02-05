from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def get_traceback():
    client = AsyncIOMotorClient('mongodb://mongo:27017')
    db = client.transcribelab
    j = await db.jobs.find_one(sort=[('created_at', -1)])
    if j:
        print("=== JOB DETAILS ===")
        print(f"ID: {j['_id']}")
        print(f"Original Filename: {j.get('original_filename')}")
        print(f"Status: {j['status']}")
        print("--- RAW STATUS MESSAGE ---")
        print(repr(j.get('status_message')))
        print("--- END ---")
    else:
        print("No jobs found")

if __name__ == "__main__":
    asyncio.run(get_traceback())
