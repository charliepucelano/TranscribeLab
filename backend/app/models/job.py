from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime
from bson import ObjectId

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobConfig(BaseModel):
    vad_onset: float = 0.4
    min_silence_duration_ms: int = 250
    max_initial_silence: float = 0.5
    min_speakers: Optional[int] = None
    max_speakers: Optional[int] = None
    beam_size: int = 5
    condition_on_previous_text: bool = False

class JobBase(BaseModel):
    job_name: Optional[str] = None
    meeting_type: str = "General Meeting"
    language: str = "en"
    
class JobCreate(JobBase):
    config: Optional[JobConfig] = None

class JobInDB(JobBase):
    user_id: str
    filename: Optional[str] = None
    original_filename: Optional[str] = None
    content_type: Optional[str] = None
    size: Optional[int] = None
    num_speakers: Optional[int] = None
    status: Optional[JobStatus] = JobStatus.PENDING
    status_message: Optional[str] = None # Granular progress: "Transcribing", "Aligning", etc.
    progress: Optional[int] = 0 # 0-100 percentage coverage
    file_path: Optional[str] = None # Path to encrypted audio
    file_key: Optional[str] = None # Encrypted/Encoded file key
    transcript_path: Optional[str] = None # Path to encrypted transcript
    transcript_text: Optional[str] = None # Stored transcript for alignment (DEPRECATED: Use transcript_file_path if it's a file)
    transcript_file_path: Optional[str] = None # Path to uploaded transcript (HiDock mode)
    config: JobConfig = Field(default_factory=JobConfig)
    duration: Optional[float] = None
    summary_encrypted: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Job(JobInDB):
    id: Optional[str] = Field(alias="_id", default=None)
    
class TranscriptUpdate(BaseModel):
    segments: list
