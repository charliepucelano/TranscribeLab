from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db.connect()
    print("Starting up TranscribeLab Backend...")
    yield
    # Shutdown
    db.close()
    print("Shutting down...")

from app.api import auth, jobs, sse, templates, utils

app = FastAPI(
    title="TranscribeLab API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://localhost:3002", # Development frontend
    f"http://{settings.DOMAIN_NAME}" if settings.DOMAIN_NAME else "*",
    f"https://{settings.DOMAIN_NAME}" if settings.DOMAIN_NAME else "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev simplicity, refine later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
from app.api import admin
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(templates.router, prefix="/templates", tags=["templates"])

app.include_router(utils.router, prefix="/utils", tags=["utils"])
app.include_router(sse.router, tags=["sse"])


@app.get("/")
async def root():
    return {"message": "Welcome to TranscribeLab API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
