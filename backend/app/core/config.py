from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "TranscribeLab"
    DOMAIN_NAME: Optional[str] = "transcribe.leyforge.com"
    
    # Database
    MONGO_URI: str = "mongodb://mongo:27017/transcribelab"
    
    # Security
    JWT_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 1 week
    
    # Services
    WHISPERX_URL: str = "http://whisperx:8000"
    OLLAMA_URL: str = "http://host.docker.internal:11434"
    HF_TOKEN: Optional[str] = None
    
    # Storage
    TRANSCRIPT_STORAGE_PATH: str = "/transcripts"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
