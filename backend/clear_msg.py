import motor.motor_asyncio
import asyncio

async def clean_job():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://mongo:27017")
    db = client.transcribelab
    # Find last job
    j = await db.jobs.find_one(sort=[('created_at', -1)])
    if j:
        print(f"Cleaning job {j['_id']}")
        # Clear status message
        await db.jobs.update_one(
            {"_id": j['_id']}, 
            {"$set": {"status_message": "Error details cleared for stability."}}
        )
        print("Status message cleared.")

if __name__ == "__main__":
    asyncio.run(clean_job())
