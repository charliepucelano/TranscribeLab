FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for some crypto/audio libs potentially)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install AI dependencies with specific versions to prevent incompatible updates
# Combining them in one RUN allows the resolver to find a compatible set
RUN pip install --no-cache-dir \
    torch==2.1.0 \
    torchaudio==2.1.0 \
    git+https://github.com/m-bain/whisperX.git \
    --extra-index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create directory for transcripts with correct permissions
RUN mkdir -p /transcripts && chmod 777 /transcripts

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010", "--reload"]
