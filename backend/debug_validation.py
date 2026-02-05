from app.models.job import JobInDB, Job
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import traceback

async def debug():
    client = AsyncIOMotorClient('mongodb://mongo:27017')
    db = client.transcribelab
    # Get the latest job (the one causing issues)
    j = await db.jobs.find_one(sort=[('created_at', -1)])
    
    if not j:
        print("No job found")
        return

    print(f"Raw Job ID: {j.get('_id')}")
    print(f"Raw Status: {j.get('status')} ({type(j.get('status'))})")
    print(f"Raw Progress: {j.get('progress')} ({type(j.get('progress'))})")

    try:
        # Pydantic expects _id to be aliased to id, but usually we unpack **j
        # Job model has id: PyObjectId = Field(alias="_id")
        model = Job(**j)
        print("Validation Successful!")
        print(model.json())
    except Exception as e:
        print("\nVALIDATION FAILED:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug())
