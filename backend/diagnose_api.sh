#!/bin/bash
export PYTHONPATH=/app

echo "--- RUNNING TRANSCRIPT DEBUG ---"
python /app/debug_transcript.py

echo "--- FETCHING JOB ID ---"
JOB_ID=$(python -c "import asyncio; from motor.motor_asyncio import AsyncIOMotorClient; client = AsyncIOMotorClient('mongodb://mongo:27017'); print(str(asyncio.run(client.transcribelab.jobs.find_one(sort=[('created_at', -1)]))['_id']))")
echo "Latest Job ID: $JOB_ID"

echo "--- CURL TESTING API (Port 80) ---"
curl -v http://localhost:80/jobs/$JOB_ID 2>&1

echo "--- CURL TESTING API (Port 8000) ---"
curl -v http://localhost:8000/jobs/$JOB_ID 2>&1
