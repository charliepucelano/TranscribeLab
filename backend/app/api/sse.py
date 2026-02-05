from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from app.api.auth import get_current_user
from app.models.user import User
from app.core.config import settings
from app.core.database import db
from bson import ObjectId
import asyncio
import json
from datetime import datetime

router = APIRouter()

# Duplicate/Custom dependency for Query Param Token
async def get_current_user_from_token(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        from jose import jwt, JWTError
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
        
    user = await db.get_db().users.find_one({"email": email})
    if user is None:
        raise credentials_exception
    return User(**user)

@router.get("/jobs/{job_id}/events")
async def job_events(
    job_id: str, 
    request: Request,
    user: User = Depends(get_current_user_from_token)
):
    """
    Server-Sent Events (SSE) endpoint for real-time job updates.
    """
    
    async def event_generator():
        # Clean up database connection usage? No, motor is async.
        
        # Initial State
        last_status = None
        last_progress = -1
        last_message = ""
        
        # Verify job ownership once
        job = await db.get_db().jobs.find_one({"_id": ObjectId(job_id), "user_id": str(user.id)})
        if not job:
            yield f"event: error\ndata: Job not found\n\n"
            return

        while True:
            if await request.is_disconnected():
                break

            # Poll Job status
            # Optimization: Use change streams instead of polling if MongoDB replica set enabled?
            # Standard Mongo container usually standalone. Polling is safer for MVP.
            
            job = await db.get_db().jobs.find_one(
                {"_id": ObjectId(job_id)},
                {"status": 1, "progress": 1, "status_message": 1}
            )
            
            if not job:
                yield f"event: error\ndata: Job lost\n\n"
                break
                
            current_status = job.get("status")
            current_progress = job.get("progress", 0)
            current_message = job.get("status_message", "")
            
            # Check for changes
            has_change = (
                current_status != last_status or 
                current_progress != last_progress or 
                current_message != last_message
            )
            
            if has_change:
                # Send Event
                data = json.dumps({
                    "status": current_status,
                    "progress": current_progress,
                    "message": current_message,
                    "timestamp": datetime.utcnow().isoformat()
                })
                yield f"data: {data}\n\n"
                
                # Update last state
                last_status = current_status
                last_progress = current_progress
                last_message = current_message
                
                # If completed or failed, we can close the stream eventually?
                # Actually, client might want to stay connected for a bit
                if current_status in ["completed", "failed"]:
                    # Maybe wait a few seconds then close?
                    # Or let client close.
                    pass

            await asyncio.sleep(1.0) # Poll every 1s

    return StreamingResponse(event_generator(), media_type="text/event-stream")
