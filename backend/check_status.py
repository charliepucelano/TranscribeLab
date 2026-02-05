from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def check():
    client = AsyncIOMotorClient('mongodb://mongo:27017')
    db = client.transcribelab
    j = await db.jobs.find_one(sort=[('created_at', -1)])
    if j:
        print(f"Status: {j.get('status')}")
        print(f"Message: {j.get('status_message')}")
        print(f"Progress: {j.get('progress')}")
    else:
        print("No job found")

if __name__ == "__main__":
    asyncio.run(check())
