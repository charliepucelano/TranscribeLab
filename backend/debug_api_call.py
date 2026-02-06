import requests
import asyncio
from app.core.database import db
from app.core.config import settings
from app.core.auth import create_access_token
import os
import sys

async def debug_api():
    try:
        db.connect()
        # 1. Get User
        user = await db.get_db().users.find_one({})
        if not user:
            print("No user found")
            return
            
        token = create_access_token({"sub": user["email"]})
        print(f"Token generated for {user['email']}")
        
        # 2. Get Last Job
        job = await db.get_db().jobs.find_one(sort=[("created_at", -1)])
        if not job:
            print("No job found")
            return
            
        job_id = str(job["_id"])
        print(f"Testing Job: {job_id}")
        
        # 3. Request Job Details via API
        headers = {"Authorization": f"Bearer {token}"}
        url = f"http://127.0.0.1:8010/jobs/{job_id}"
        
        print(f"GET {url}")
        res = requests.get(url, headers=headers)
        print(f"Status: {res.status_code}")
        print("Response Body:")
        print(res.text)
        
    except Exception as e:
        print(f"Script Error: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(debug_api())
