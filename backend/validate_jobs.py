import motor.motor_asyncio
import asyncio
from app.models.job import Job
from bson import ObjectId

async def validate_all_jobs():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://mongo:27017")
    db = client.transcribelab
    
    print("\n--- Validating All Jobs ---")
    async for job_data in db.jobs.find():
        jid = str(job_data["_id"])
        uid = job_data.get("user_id")
        uid_type = str(type(uid))
        print(f"Checking Job {jid} - UserID Type: {uid_type}")
        try:
            # Manually handle _id
            job_data["_id"] = jid
            Job(**job_data)
        except Exception as e:
            print(f"❌ Job {jid} FAILED validation:")
            print(f"   UserID Value: {uid}")
            print(f"   Error: {e}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(validate_all_jobs())
