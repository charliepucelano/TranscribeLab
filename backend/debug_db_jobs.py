
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from app.models.job import Job
from pydantic import ValidationError

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/transcribelab")

async def validate_all_jobs():
    print("Connecting to DB...")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.transcribelab
    
    print("Fetching ALL jobs...")
    jobs_cursor = db.jobs.find({})
    jobs = await jobs_cursor.to_list(1000)
    
    print(f"Found {len(jobs)} jobs.")
    
    success_count = 0
    fail_count = 0
    
    for i, job_doc in enumerate(jobs):
        try:
            # print(f"Validating Job {i}: ID={job_doc.get('_id')}")
            job = Job(**job_doc)
            # Try to dump to ensure serialization works
            json_output = job.model_dump_json()
            success_count += 1
        except ValidationError as e:
            print(f"!!! VALIDATION ERROR on Job {job_doc.get('_id')} !!!")
            print(e)
            fail_count += 1
        except Exception as e:
            print(f"!!! OTHER ERROR on Job {job_doc.get('_id')} !!!")
            print(e)
            fail_count += 1
            
    print(f"--- SUMMARY ---")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")

if __name__ == "__main__":
    asyncio.run(validate_all_jobs())
