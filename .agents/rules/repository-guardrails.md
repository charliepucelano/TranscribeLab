---
trigger: always_on
---

# TranscribeLab Repository Guardrails

## Rules
1. Maintain separation between Python FastAPI backend and Next.js frontend.
2. Keep PyTorch / Whisper inference off the main async event loop (use worker threads/tasks).
3. Preserve MongoDB schema structure in `backend/app/models/`.
