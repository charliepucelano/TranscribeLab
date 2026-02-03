FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for some crypto/audio libs potentially)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create directory for transcripts with correct permissions
RUN mkdir -p /transcripts && chmod 777 /transcripts

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010", "--reload"]
