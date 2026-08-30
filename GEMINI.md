# TranscribeLab — Antigravity Workspace Guide

Full-stack audio transcription, speaker diarization, and meeting summarization platform using FastAPI, Next.js, Whisper, pyannote, and MongoDB.

## Architecture & Ports
- **Frontend**: Next.js on Port `3002` (via `tdev` / `tstopdev`)
- **Backend API**: FastAPI on Port `8002` (via Docker `transcribelab-backend`)
- **Database**: MongoDB on Port `27017` (Docker `transcribelab-mongo`)
- **Stack Management**: `tstart` / `tstop` / `tstatus` / `tlogs`

## Project Rules & BMAD Layer
Rules are located in `.agents/rules/`:
- `repository-guardrails.md`: Service separation, async task handling.
- `transcription-pipeline.md`: Whisper model caching, diarization chunking, memory optimization.

## Core Invariants
1. **Docker Service Lifecycle**: Use `manage.ps1` or aliases (`tstart`, `tstop`, `trestartbackend`).
2. **Audio File Handling**: Stream or chunk large audio uploads to prevent memory exhaustion.
