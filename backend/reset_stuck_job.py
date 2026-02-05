from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def reset():
    client = AsyncIOMotorClient('mongodb://mongo:27017')
    db = client.transcribelab
    # Find latest job
    j = await db.jobs.find_one(sort=[('created_at', -1)])
    if not j:
        print("No job")
        return
        
    print(f"Resetting Job {j['_id']}")
    # Reset to COMPLETED but with error message
    await db.jobs.update_one(
        {'_id': j['_id']},
        {'$set': {
            'status': 'completed',
            'status_message': 'Diarization Canceled (Process Stopped)',
            'progress': 100
        }}
    )
    print("Done")

if __name__ == "__main__":
    asyncio.run(reset())
