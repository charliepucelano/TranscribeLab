
import asyncio
from app.core.database import db
from app.api.jobs import get_job
from app.models.user import User
from bson import ObjectId

class MockUser:
    id = ObjectId("65bb...mock...") # Doesn't matter for this check if we bypass dependency

async def debug_get_job():
    db.connect()
    # Fetch the first job ID dynamically
    j = await db.get_db().jobs.find_one({})
    if not j:
        print("No jobs.")
        return
    job_id = str(j["_id"])
    print(f"Testing GET /jobs/{job_id}")
    
    # Manually query DB to see raw
    print(f"RAW DB: {j}")
    
    # We can't easily invoke the router function directly due to Dependency Injection of `current_user`.
    # But we can verify what pydantic does.
    from app.models.job import Job
    try:
        pydantic_job = Job(**j)
        print(f"Pydantic Dump: {pydantic_job.model_dump()}")
        print(f"Status in Model: {pydantic_job.status}")
    except Exception as e:
        print(f"Model Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_get_job())
