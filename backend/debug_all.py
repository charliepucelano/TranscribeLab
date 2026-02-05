from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from app.models.job import Job
import traceback

async def debug_all():
    client = AsyncIOMotorClient('mongodb://mongo:27017')
    db = client.transcribelab
    
    print("\n=== SCANNING ALL JOBS FOR ERRORS ===")
    async for j in db.jobs.find().sort("created_at", -1):
        jid = str(j['_id'])
        print(f"\nJob ID: {jid}")
        print(f"Status: {j.get('status')}")
        
        # Check for error message in DB
        msg = j.get('status_message')
        if msg:
            print("--- DATABASE TRACEBACK ---")
            print(msg)  # This should print the full multiline string I saved
            print("--- END ---")
        
        # Check for Pydantic validation error (Dashboard 500 trigger)
        try:
            j_copy = j.copy()
            j_copy['_id'] = str(j_copy['_id'])
            Job(**j_copy)
            print("✅ Pydantic Validation: PASSED")
        except Exception as e:
            print("❌ Pydantic Validation: FAILED")
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_all())
