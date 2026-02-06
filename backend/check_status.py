from app.core.database import db
from app.core.config import settings
import asyncio
import os

async def check():
    print(f"Connecting to DB at: {settings.MONGO_URI}")
    try:
        db.connect()
        # Simple ping or find
        count = await db.get_db().jobs.count_documents({})
        print(f"DB Connected. Total Jobs: {count}")
        
        # Check last job details
        last_job = await db.get_db().jobs.find_one(sort=[("created_at", -1)])
        if last_job:
            print(f"Last Job Status: {last_job.get('status')}")
            print(f"Last Job Msg: {last_job.get('status_message')}")
        
    except Exception as e:
        print(f"DB Connection Failed: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check())
