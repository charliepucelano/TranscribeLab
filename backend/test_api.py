import urllib.request
import urllib.error
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def fetch_job():
    # Force minimal deps
    client = AsyncIOMotorClient('mongodb://mongo:27017')
    db = client.transcribelab
    j = await db.jobs.find_one(sort=[('created_at', -1)])
    if not j:
        print("No job")
        return
        
    job_id = str(j['_id'])
    print(f"Fetching Job ID: {job_id}")
    
    # Try Port 80
    print("--- TRYING PORT 80 ---")
    try:
        url = f"http://localhost:80/jobs/{job_id}"
        req = urllib.request.Request(url)
        # Add basic auth headers if needed? No, internal.
        # But wait, endpoint expects User? 
        # current_user = Depends(get_current_user)
        # Auth relies on JWT.
        # I cannot easily generate a JWT here without specific key.
        # HOWEVER, if I get 401 Unauthorized, that confirms the server IS running and model validation isn't the first blocker.
        # If I get 500 even without Auth? Unlikely.
        # The user's browser sends the token.
        
        # If I can't auth, I can't reach the endpoint logic that fails.
        pass
    except:
        pass

    # The user is getting 500. This implies they are Authenticated.
    # The 500 happens inside the endpoint.
    
    # I can mock the dependency? No.
    
    # Alternative: I check uvicorn logs for the traceback.
    # The traceback IS there, I just need to find it.
    
    print("Cannot simulate Auth easily. Checking uvicorn logs locally would be better.")

if __name__ == "__main__":
    asyncio.run(fetch_job())
