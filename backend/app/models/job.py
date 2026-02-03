from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from bson import ObjectId
from app.models.user import PyObjectId

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class MeetingType(str, Enum):
    GENERAL = "General Meeting"
    INTERVIEW = "Interview"
    STANDUP = "Team Standup"
    CLIENT = "Client Call"
    SALES = "Sales Call"
    BRAINSTORM = "Brainstorming Session"
    OTHER = "Other"

class JobBase(BaseModel):
    filename: str
    original_filename: str
    content_type: str
    size: int
    language: str = "en"
    num_speakers: Optional[int] = None # 0 or None for auto
    meeting_type: MeetingType = MeetingType.GENERAL
    job_name: Optional[str] = None
    
class JobCreate(JobBase):
    pass

class JobInDB(JobBase):
    user_id: str
    status: JobStatus = JobStatus.PENDING
    file_path: str # Path to encrypted audio
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    speaker_labels: Optional[List[str]] = None
    duration: Optional[float] = None
    
class Job(JobInDB):
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
