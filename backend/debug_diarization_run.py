from app.services.transcription import transcription_service
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
import logging
import sys

# Setup Logging to Stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

async def run_diarization_debug():
    client = AsyncIOMotorClient('mongodb://mongo:27017')
    db = client.transcribelab
    # Find latest job
    j = await db.jobs.find_one(sort=[('created_at', -1)])
    if not j:
        print("No job found")
        return
        
    job_id = str(j['_id'])
    print(f"--- STARTING DEBUG DIARIZATION FOR {job_id} ---")
    print(f"Current Status: {j.get('status')}")
    print(f"Current Message: {j.get('status_message')}")
    
    # Force run
    try:
        await transcription_service.process_diarization_only(job_id)
        print("--- DIARIZATION COMPLETED SUCCESSFULLY ---")
    except Exception as e:
        print(f"--- DIARIZATION CRASHED: {e} ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_diarization_debug())
