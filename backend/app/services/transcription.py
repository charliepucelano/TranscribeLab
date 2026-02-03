import os
import httpx
import json
import logging
from typing import Optional, List
from app.core.config import settings
from app.core.database import db
from app.core.crypto import decrypt_data, decode_str, encrypt_data, encode_bytes, generate_key
from app.models.job import JobStatus, JobInDB
from bson import ObjectId
from datetime import datetime

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self):
        self.whisper_url = f"{settings.WHISPERX_URL}/v1/audio/transcriptions"
        # whisperx container might be OpenAI compatible at /v1/audio/transcriptions
        # dependent on the image used. fedirz/faster-whisper-server is OpenAI compatible.

    async def process_job(self, job_id: str):
        """
        Main entry point for background processing of a job.
        """
        logger.info(f"Starting processing for job {job_id}")
        
        # 1. Fetch Job
        job = await db.get_db().jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        # Update status to PROCESSING
        await db.get_db().jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"status": JobStatus.PROCESSING, "started_at": datetime.utcnow()}}
        )

        try:
            # 2. Decrypt Audio File
            # Get the File Key (Temporary mechanism from Phase 2)
            # In a real scenario, this would be unwrapped with Master Key.
            encrypted_file_key = job.get("file_key")
            file_key = decode_str(encrypted_file_key)
            
            file_path = job["file_path"]
            with open(file_path, "rb") as f:
                encrypted_content = f.read()
            
            audio_data = decrypt_data(encrypted_content, file_key)
            
            # 3. Send to WhisperX
            # We need to send 'file' as multipart/form-data
            # We'll use a temporary filename in the memory buffer because some APIs verify extension
            files = {
                'file': (job["original_filename"], audio_data, job["content_type"])
            }
            
            data = {
                "model": "large-v3",
                "response_format": "verbose_json", # To get segments and timestamps
                # "language": job["language"] # Optional, let auto-detect or force
            }
            if job.get("language"):
                data["language"] = job["language"]
                
            # If using custom WhisperX server params might differ, but for OpenAI compat:
            async with httpx.AsyncClient(timeout=1200.0) as client: # Long timeout for audio
                logger.info(f"Sending request to {self.whisper_url}")
                response = await client.post(self.whisper_url, files=files, data=data)
                
                if response.status_code != 200:
                    logger.error(f"WhisperX Error: {response.text}")
                    raise Exception(f"Transcription failed: {response.text}")
                
                result = response.json()
            
            # 4. Process Results (Attributes depends on exact response format)
            # Standard OpenAI verbose_json has 'segments'
            segments = result.get("segments", [])
            transcript_text = result.get("text", "")
            
            # Extract speaker labels if available (diarization)
            # OpenAI API doesn't standardly return speaker labels unless it's a specific fork
            # fedirz/faster-whisper-server supports 'diarization_min_speakers' etc params if enabled?
            # Actually, standard Whisper doesn't do diarization. WhisperX DOES.
            # Does the container endpoint support it?
            # If using 'whisperx' image, usually it's a python script or custom API. 
            # If using 'fedirz/faster-whisper-server', it doesn't do diarization by default without params.
            # Assuming basic transcription first.
            
            # 5. Encrypt Transcript
            # We use the SAME File Key for now? Or generate a new Transcript Key?
            # Simpler to reuse File Key for the Job bundle.
            transcript_json = json.dumps(result).encode('utf-8')
            encrypted_transcript = encrypt_data(transcript_json, file_key)
            
            transcript_filename = f"{job['filename']}.json.enc"
            transcript_path = os.path.join(os.path.dirname(file_path), transcript_filename)
            
            with open(transcript_path, "wb") as f:
                f.write(encrypted_transcript)
                
            # 6. Update Job
            duration = result.get("duration", 0) # Top level duration
            
            await db.get_db().jobs.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": {
                    "status": JobStatus.COMPLETED,
                    "completed_at": datetime.utcnow(),
                    "transcript_path": transcript_path, # Path to encrypted result
                    "duration": duration
                }}
            )
            logger.info(f"Job {job_id} completed successfully")

        except Exception as e:
            logger.exception(f"Error processing job {job_id}: {e}")
            await db.get_db().jobs.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": {"status": JobStatus.FAILED}}
            )

transcription_service = TranscriptionService()
