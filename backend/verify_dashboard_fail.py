import motor.motor_asyncio
import asyncio
from app.models.job import Job
from bson import ObjectId
import traceback

async def check():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://mongo:27017")
    db = client.transcribelab
    
    print("Checking jobs for validation errors...")
    async for j in db.jobs.find().sort("created_at", -1):
        print(f"Checking Job {j.get('_id')}")
        try:
            # Check for NaNs
            import math
            for k, v in j.items():
                if isinstance(v, float) and math.isnan(v):
                    print(f"  WARNING: Field {k} is NaN!")
            
            # Fix ID
            j['_id'] = str(j['_id'])
            # Validate
            Job(**j)
            print("  OK")
        except Exception as e:
            print(f"  FAIL: {e}")
            print(f"  Data: {j}")
            break

if __name__ == "__main__":
    asyncio.run(check())
