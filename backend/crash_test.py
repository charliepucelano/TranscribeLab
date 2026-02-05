
import asyncio
from app.core.database import db
from app.api.jobs import list_jobs
from app.models.user import User
from bson import ObjectId

# Mock User
class MockUser:
    id = ObjectId()

async def crash_test():
    print("Connecting...")
    try:
        db.connect()
        print("Connected.")
    except Exception as e:
        print(f"Connect Logic Failed: {e}")
        
    print("Getting DB...")
    try:
        database = db.get_db()
        print(f"DB Name: {database.name}")
    except Exception as e:
        print(f"get_db Failed: {e}")
        return

    print("Running Query...")
    try:
        # Replicate logic: jobs = await db.get_db().jobs.find({"user_id": str(current_user.id)}).sort("created_at", -1).to_list(100)
        jobs = await database.jobs.find({}).to_list(10)
        print(f"Found {len(jobs)} jobs")
        for job in jobs:
            print(f" - {job.get('job_name')}")
    except Exception as e:
        print(f"Query Failed: {e}")

if __name__ == "__main__":
    asyncio.run(crash_test())
