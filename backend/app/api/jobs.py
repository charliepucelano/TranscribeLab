from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from app.api.auth import get_current_user
from app.models.user import User
from app.models.job import Job, JobCreate, JobInDB, JobStatus, JobConfig
from app.core.database import db
from app.core.config import settings
from app.core.crypto import generate_key, encrypt_data, encode_bytes, decode_str, decrypt_data
import os
import shutil
import json
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from app.services.transcription import transcription_service
from app.services.summarization import generate_summary, get_style_guide

router = APIRouter()

@router.post("/upload", response_model=Job)
async def create_job(
    file: UploadFile = File(...),
    transcript_file: Optional[UploadFile] = File(None), # Optional transcript for alignment
    language: str = Form("en"),
    num_speakers: Optional[int] = Form(None),
    config: Optional[str] = Form(None), # JSON string of configuration
    meeting_type: str = Form("General Meeting"),
    job_name: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(), # Correct way to use it in FastAPI
    current_user: User = Depends(get_current_user)
):
    # Default job name if still empty
    if not job_name:
        job_name = file.filename

    # Convert meeting_type string to enum
    try:
        meeting_type_enum = MeetingType(meeting_type)
    except ValueError:
        meeting_type_enum = MeetingType.GENERAL

    # Parse Config
    job_config = JobConfig()
    if config:
        try:
            config_dict = json.loads(config)
            # Create config object, overriding defaults with user input
            job_config = JobConfig(**config_dict)
        except Exception as e:
            print(f"Error parsing config: {e}")
            # Fallback to default, or we could raise error. 
            # For now warning only.

    # 1. Prepare storage path
    user_dir = os.path.join(settings.TRANSCRIPT_STORAGE_PATH, "users", str(current_user.id))
    upload_dir = os.path.join(user_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate Key
    file_key = generate_key()
    
    # Save and Encrypt Audio
    filename = f"{datetime.utcnow().timestamp()}_{file.filename}"
    file_path = os.path.join(upload_dir, filename + ".enc")
    
    temp_path = file_path + ".tmp"
    total_received = 0
    try:
        with open(temp_path, "wb") as f:
            while chunk := await file.read(1024 * 512):
                f.write(chunk)
                total_received += len(chunk)
        
        # Encrypt Audio
        with open(temp_path, "rb") as f:
            file_content = f.read()
        encrypted_content = encrypt_data(file_content, file_key)
        with open(file_path, "wb") as f:
            f.write(encrypted_content)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    # Handle Transcript File (HiDock Mode)
    transcript_file_path_enc = None
    transcript_text_content = None # Legacy support
    
    if transcript_file:
        try:
            # We encrypt this too using same key
            tf_name = f"{datetime.utcnow().timestamp()}_transcript_{transcript_file.filename}"
            tf_path_enc = os.path.join(upload_dir, tf_name + ".enc")
            
            tf_content = await transcript_file.read()
            # Try to populate legacy text field for immediate viewing if text/srt
            try:
                transcript_text_content = tf_content.decode("utf-8")
            except:
                pass
                
            tf_enc = encrypt_data(tf_content, file_key)
            with open(tf_path_enc, "wb") as f:
                f.write(tf_enc)
                
            transcript_file_path_enc = tf_path_enc
        except Exception as e:
            raise HTTPException(status_code=400, detail="Error processing transcript file.")

    job = JobInDB(
        filename=filename,
        original_filename=file.filename,
        content_type=file.content_type,
        size=len(encrypted_content),
        file_path=file_path,
        language=language,
        num_speakers=num_speakers if num_speakers and num_speakers > 0 else None,
        meeting_type=meeting_type_enum,
        user_id=str(current_user.id),
        file_key=encode_bytes(file_key),
        job_name=job_name,
        transcript_text=transcript_text_content,
        transcript_file_path=transcript_file_path_enc,
        config=job_config,
        status=JobStatus.PENDING
    )
    
    job_dict = job.model_dump(by_alias=True, exclude={"id"})
    
    new_job = await db.get_db().jobs.insert_one(job_dict)
    created_job = await db.get_db().jobs.find_one({"_id": new_job.inserted_id})
    
    # Trigger Background Transcription
    background_tasks.add_task(transcription_service.process_job, str(new_job.inserted_id))
    
    return Job(**created_job)

@router.get("", response_model=List[Job])
async def list_jobs(current_user: User = Depends(get_current_user)):
    try:
        print(f"Listing jobs for user {current_user.id}")
        jobs_data = await db.get_db().jobs.find({"user_id": str(current_user.id)}).sort("created_at", -1).to_list(100)
        print(f"Found {len(jobs_data)} jobs")
        
        results = []
        for job_data in jobs_data:
            try:
                # Ensure _id is handled if not already
                if "_id" in job_data and not isinstance(job_data["_id"], str):
                    job_data["_id"] = str(job_data["_id"])
                
                results.append(Job(**job_data))
            except Exception as val_e:
                print(f"SKIP JOB {job_data.get('_id')}: Validation failed: {val_e}")
                import traceback
                traceback.print_exc()
                
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRITICAL ERROR IN LIST_JOBS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{job_id}/retry", response_model=Job)
async def retry_job(
    job_id: str, 
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user)
):
    job = await db.get_db().jobs.find_one({"_id": ObjectId(job_id), "user_id": str(current_user.id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Check if audio file still exists
    if not job.get("file_path") or not os.path.exists(job["file_path"]):
        raise HTTPException(status_code=400, detail="Original audio file missing. Cannot retry.")

    # Reset job status in DB
    await db.get_db().jobs.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {
            "status": JobStatus.PENDING,
            "status_message": "Retrying...",
            "progress": 0
        }}
    )

    # Re-trigger background task
    background_tasks.add_task(transcription_service.process_job, job_id)
    
    updated_job = await db.get_db().jobs.find_one({"_id": ObjectId(job_id)})
    return Job(**updated_job)

@router.post("/{job_id}/diarize", response_model=Job)
async def diarize_job(
    job_id: str, 
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user)
):
    try:
        job = await db.get_db().jobs.find_one({"_id": ObjectId(job_id), "user_id": str(current_user.id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
            
        if not job.get("transcript_path"):
            raise HTTPException(status_code=400, detail="Transcript must be ready before diarization")
            
        # Trigger background task
        background_tasks.add_task(transcription_service.process_diarization_only, job_id)
        
        # Update status immediately
        await db.get_db().jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"status_message": "Queued for Diarization..."}}
        )
        
        updated_job = await db.get_db().jobs.find_one({"_id": ObjectId(job_id)})
        
        # Safe conversion for Pydantic
        if updated_job:
            updated_job["_id"] = str(updated_job["_id"])
            
        return Job(**updated_job)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in diarize_job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to queue diarization: {str(e)}")

@router.delete("/{job_id}")
async def delete_job(job_id: str, current_user: User = Depends(get_current_user)):
    # 1. Fetch job to get file paths
    job = await db.get_db().jobs.find_one({"_id": ObjectId(job_id), "user_id": str(current_user.id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # 2. Delete files from disk
    paths_to_delete = [job.get("file_path"), job.get("transcript_path")]
    for path in paths_to_delete:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Error deleting file {path}: {e}")
                
    # 3. Delete from DB
    await db.get_db().jobs.delete_one({"_id": ObjectId(job_id)})
    return None

@router.get("/{job_id}", response_model=Job)
async def get_job(job_id: str, current_user: User = Depends(get_current_user)):
    job = await db.get_db().jobs.find_one({"_id": ObjectId(job_id), "user_id": str(current_user.id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    try:
        # Convert _id to string for Pydantic if needed
        job["_id"] = str(job["_id"])
        
        # DEBUG: Print job content to logs to debug validation error
        # print(f"DEBUG JOB for {job_id}: {job}") 
        
        return Job(**job)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"!!! Pydantic Validation Error for job {job_id}: {e}")
        # Print detailed validation errors if it's a Pydantic error
        if hasattr(e, 'errors'):
             print(f"Validation Details: {e.errors()}")
        print(f"Failing Data: {job}")
        try:
            # Return a fallback to keep UI alive
            return Job(
                id=str(job["_id"]), 
                user_id=str(job["user_id"]), 
                job_name=job.get("job_name", "Unknown Job"),
                meeting_type=job.get("meeting_type", "General"),
                language=job.get("language", "en"),
                config=JobConfig(), # Provide default config
                status=JobStatus.FAILED,
                status_message=f"Data Validation Error: {str(e)[:100]}",
                progress=0
            )
        except Exception as fallback_e:
             print(f"FATAL: Fallback creation failed: {fallback_e}")
             traceback.print_exc()
             raise HTTPException(status_code=500, detail=f"Critical Data Error: {e}")

@router.get("/{job_id}/transcript")
async def get_job_transcript(job_id: str, current_user: User = Depends(get_current_user)):
    job = await db.get_db().jobs.find_one({"_id": ObjectId(job_id), "user_id": str(current_user.id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.get("status") != JobStatus.COMPLETED or not job.get("transcript_path"):
        raise HTTPException(status_code=400, detail="Transcript not ready")
        
    # Decrypt Transcript
    try:
        encrypted_file_key = job.get("file_key")
        if not encrypted_file_key:
            raise HTTPException(status_code=500, detail="Encryption key missing for this job. Data may be lost.")
            
        file_key = decode_str(encrypted_file_key)
        
        transcript_path = job["transcript_path"]
        if not os.path.exists(transcript_path):
             raise HTTPException(status_code=404, detail="Transcript file missing from disk")
             
        with open(transcript_path, "rb") as f:
            encrypted_content = f.read()
            
        decrypted_json_bytes = decrypt_data(encrypted_content, file_key)
        transcript_data = json.loads(decrypted_json_bytes.decode('utf-8'))
        
        # DEBUG: Check structure
        print(f"DEBUG TRANSCRIPT for {job_id}. Keys: {list(transcript_data.keys())}")
        if "segments" in transcript_data:
             print(f"Segment count: {len(transcript_data['segments'])}")
             if len(transcript_data['segments']) > 0:
                 print(f"Sample segment: {transcript_data['segments'][0]}")
        else:
             print("CRITICAL: 'segments' key missing in transcript data!")
        
        return transcript_data
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error decrypting transcript: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to decrypt transcript: {type(e).__name__} - {str(e)}")

from app.models.job import TranscriptUpdate

@router.put("/{job_id}/transcript")
async def update_transcript(job_id: str, update: TranscriptUpdate, current_user: User = Depends(get_current_user)):
    job = await db.get_db().jobs.find_one({"_id": ObjectId(job_id), "user_id": str(current_user.id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if not job.get("transcript_path"):
        raise HTTPException(status_code=400, detail="Original transcript not found")

    try:
        # 1. Get Key
        encrypted_file_key = job.get("file_key")
        if not encrypted_file_key:
             raise HTTPException(status_code=500, detail="Encryption key missing.")
        file_key = decode_str(encrypted_file_key)
        
        # 2. Reconstruct full structure
        # segments might be dicts or objects depending on Pydantic
        # Since TranscriptUpdate defines segments as list, they are likely dicts
        
        # full_text = " ".join([s.get("text", "") if isinstance(s, dict) else s.text for s in update.segments])
        
        seg_list = []
        full_text_parts = []
        
        for s in update.segments:
            s_dict = s if isinstance(s, dict) else s.model_dump()
            seg_list.append(s_dict)
            full_text_parts.append(s_dict.get("text", ""))
            
        full_text = " ".join(full_text_parts)
        
        transcript_data = {
            "segments": seg_list,
            "language": job.get("language", "en"),
            "text": full_text
        }
        
        # 3. Encrypt
        result_json = json.dumps(transcript_data).encode('utf-8')
        encrypted_transcript = encrypt_data(result_json, file_key)
        
        # 4. Save to Disk (Overwrite)
        transcript_path = job["transcript_path"]
        with open(transcript_path, "wb") as f:
            f.write(encrypted_transcript)
            
        return {"status": "updated", "segment_count": len(update.segments)}

    except Exception as e:
        print(f"Error updating transcript: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update transcript: {e}")

@router.post("/{job_id}/summarize")
async def summarize_job(job_id: str, current_user: User = Depends(get_current_user)):
    job = await db.get_db().jobs.find_one({"_id": ObjectId(job_id), "user_id": str(current_user.id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.get("status") != JobStatus.COMPLETED or not job.get("transcript_path"):
        raise HTTPException(status_code=400, detail="Transcript must be ready before summarization")
        
    # 1. Decrypt Transcript
    try:
        encrypted_file_key = job.get("file_key")
        file_key = decode_str(encrypted_file_key)
        
        transcript_path = job["transcript_path"]
        with open(transcript_path, "rb") as f:
            encrypted_content = f.read()
        
        decrypted_json_bytes = decrypt_data(encrypted_content, file_key)
        transcript_data = json.loads(decrypted_json_bytes.decode('utf-8'))
        
        # Combine segments into full text
        # Combine segments into full text WITH Speaker attribution
        # We ignore top-level 'text' because it lacks speaker labels
        segments = transcript_data.get("segments", [])
        if segments:
            full_text = "\n".join([f"{s.get('speaker', 'Unknown')}: {s.get('text', '')}" for s in segments])
        else:
             full_text = transcript_data.get("text", "")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to decrypt transcript: {e}")

    # 2. Generate Summary
    meeting_type = job.get("meeting_type", "General Meeting")
    language = job.get("language", "en")
    summary = await generate_summary(full_text, meeting_type=meeting_type, language=language)
    
    # 3. Store Summary (Encrypted)
    summary_bytes = summary.encode('utf-8')
    encrypted_summary = encrypt_data(summary_bytes, file_key)
    encrypted_summary_str = encode_bytes(encrypted_summary) # Store as base64 string
    
    await db.get_db().jobs.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {"summary_encrypted": encrypted_summary_str}}
    )
    
    return {"status": "summary_generated"}

@router.get("/{job_id}/summary")
async def get_job_summary(job_id: str, current_user: User = Depends(get_current_user)):
    job = await db.get_db().jobs.find_one({"_id": ObjectId(job_id), "user_id": str(current_user.id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    encrypted_summary_str = job.get("summary_encrypted")
    if not encrypted_summary_str:
        return {"summary": None}
        
    try:
        encrypted_file_key = job.get("file_key")
        file_key = decode_str(encrypted_file_key)
        
        encrypted_summary = decode_str(encrypted_summary_str) # Decode base64 to bytes
        decrypted_summary_bytes = decrypt_data(encrypted_summary, file_key)
        summary = decrypted_summary_bytes.decode('utf-8')
        
        return {"summary": summary}
    except Exception as e:
        print(f"Summary decryption error: {e}")
        return {"summary": "Error: Could not decrypt summary."}
