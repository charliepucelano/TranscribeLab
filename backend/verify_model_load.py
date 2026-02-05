from app.models.job import JobInDB
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def test():
    client = AsyncIOMotorClient("mongodb://mongo:27017")
    db = client.transcribelab
    cursor = db.jobs.find({})
    count = 0
    async for doc in cursor:
        try:
            # We must convert _id to str if the model expects str for user_id logic etc?
            # JobInDB doesn't have _id field, Job does. JobInDB has user_id.
            # doc has _id as ObjectId.
            # doc has user_id as str.
            j = JobInDB(**doc)
            count += 1
            # print(f"Job {doc.get('_id')} OK")
        except Exception as e:
            print(f"Job {doc.get('_id')} FAIL: {e}")
            import traceback
            traceback.print_exc()
    print(f"Verified {count} jobs successfully.")

if __name__ == "__main__":
    asyncio.run(test())
