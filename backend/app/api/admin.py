
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.api.dependencies import get_current_active_superuser
from app.models.user import User
from app.core.database import db
from bson import ObjectId

router = APIRouter()

@router.get("/users", response_model=List[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
):
    users_cursor = db.get_db().users.find().skip(skip).limit(limit)
    users = await users_cursor.to_list(length=limit)
    return [User(**user) for user in users]

@router.get("/jobs")
async def read_all_jobs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
):
    # Fetch all jobs, but exclude sensitive fields if necessary (though jobs are usually just metadata)
    # We want to show WHO owns the job
    pipeline = [
        {"$skip": skip},
        {"$limit": limit},
        {"$addFields": {"jobId": {"$toString": "$_id"}}},
        {"$lookup": {
            "from": "users",
            "localField": "user_id",
            "foreignField": "email", # jobs store user_id as email in this app? let's check. 
            # Actually jobs usually store string ID or email. 
            # In jobs.py: `user_id = current_user.email` (typically)
            # Let's just return the raw job data for now, the frontend can display it.
            "as": "user_info"
        }}
    ]
    # Simple find is safer/faster if we don't need joins yet
    jobs_cursor = db.get_db().jobs.find().sort("created_at", -1).skip(skip).limit(limit)
    jobs = await jobs_cursor.to_list(length=limit)
    
    # Convert ObjectIds to strings
    for job in jobs:
        job["id"] = str(job["_id"])
        job["_id"] = str(job["_id"])
        
    return jobs

from app.core.config import settings
import shutil
import os
from app.core.security import get_password_hash
from pydantic import BaseModel

class ResetPasswordAdminRequest(BaseModel):
    new_password: str

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_active_superuser),
):
    try:
        # 1. Check if user exists
        user = await db.get_db().users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent self-deletion (failsafe)
        if str(user["_id"]) == str(current_user.id):
             raise HTTPException(status_code=400, detail="Cannot delete your own admin account.")

        # 2. Delete all jobs associated with this user
        # We need to find them first to delete files if they aren't in the user folder structure
        # (But they ARE in user folder structure: /transcripts/users/{user_id})
        
        # However, let's clean up DB records first
        delete_jobs_result = await db.get_db().jobs.delete_many({"user_id": str(user_id)})
        print(f"Deleted {delete_jobs_result.deleted_count} jobs for user {user_id}")

        # 3. Delete User Record
        delete_user_result = await db.get_db().users.delete_one({"_id": ObjectId(user_id)})
        
        # 4. Delete User Directory (Files)
        user_dir = os.path.join(settings.TRANSCRIPT_STORAGE_PATH, "users", str(user_id))
        if os.path.exists(user_dir):
            try:
                shutil.rmtree(user_dir)
                print(f"Deleted storage directory for user {user_id}: {user_dir}")
            except Exception as e:
                print(f"Error deleting user directory {user_dir}: {e}")
                # Don't fail the request if file deletion fails, but log it
        
        return {"message": f"User {user.get('email')} and all associated data deleted."}
    except Exception as e:
         print(f"Error deleting user {user_id}: {e}")
         raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

@router.post("/users/{user_id}/reset-password")
async def reset_user_password_admin(
    user_id: str,
    request: ResetPasswordAdminRequest,
    current_user: User = Depends(get_current_active_superuser),
):
    # 1. Check user
    user = await db.get_db().users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # 2. Update Password
    # WARNING: This invalidates the encrypted_master_key because we can't re-encrypt it 
    # without the old password. The user will effectively lose access to old files 
    # unless they use their Recovery Key to 'Recover' (Re-Key) account.
    
    await db.get_db().users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "hashed_password": get_password_hash(request.new_password),
            "force_password_change": True
        }}
    )
    
    return {"message": "Password reset successfully. User must use Recovery Key to regain access to old encrypted files."}
