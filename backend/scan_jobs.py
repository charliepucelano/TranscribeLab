import asyncio
from app.core.database import db
from app.core.config import settings
from bson import ObjectId
import os

async def scan():
    db.connect()
    print("Scanning all jobs for integrity...")
    
    cursor = db.get_db().jobs.find({})
    jobs = await cursor.to_list(length=1000)
    
    broken_count = 0
    valid_count = 0
    
    for job in jobs:
        jid = str(job["_id"])
        status = job.get("status")
        
        if status != "completed":
            continue
            
        issues = []
        if not job.get("transcript_path"):
            issues.append("Missing transcript_path")
        elif not os.path.exists(job["transcript_path"]):
            issues.append(f"File missing at {job['transcript_path']}")
            
        if not job.get("file_key"):
            issues.append("Missing file_key")
            
        if issues:
            print(f"BROKEN Job {jid}: {', '.join(issues)}")
            broken_count += 1
        else:
            valid_count += 1
            
    print(f"Scan complete. Valid: {valid_count}, Broken: {broken_count}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(scan())
