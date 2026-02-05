import os
import json
import logging
from typing import Optional, List
from app.core.config import settings
from app.core.database import db
from app.core.crypto import decrypt_data, decode_str, encrypt_data, encode_bytes, generate_key
from app.models.job import JobStatus, JobInDB
from bson import ObjectId
from datetime import datetime
import whisperx
import whisperx.diarize
import torch
import gc

# Patch for PyTorch 2.6+ to allow loading models with custom globals (trusted source)
import torch
import os

# 1. Force weights_only=False globally for any torch.load call
original_torch_load = torch.load
def patched_torch_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return original_torch_load(*args, **kwargs)
torch.load = patched_torch_load

# 2. Also register safe globals just in case some code bypasses torch.load or uses a different unpickler
if hasattr(torch.serialization, 'add_safe_globals'):
    try:
        import omegaconf
        import omegaconf.listconfig
        import omegaconf.dictconfig
        import omegaconf.base
        torch.serialization.add_safe_globals([
            omegaconf.listconfig.ListConfig, 
            omegaconf.dictconfig.DictConfig,
            omegaconf.base.ContainerMetadata,
            omegaconf.base.Metadata
        ])
    except (ImportError, AttributeError):
        pass

# 3. Set environment variable for deep bypass
os.environ["TORCH_SKIP_WEIGHTS_ONLY_CHECK"] = "1"


logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self):
        # We will load models on demand to save memory when idle, 
        # or we could cache them. For CPU "large-v3", probably safer to load/unload 
        # or keep loaded if frequent.
        # User requested better quality.
        # We upgrade to 'large-v3' (or 'large-v2') as default for high-end systems (128GB RAM).
        # We keep int8 for speed, but float16 is better if GPU available.
        import torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if self.device == "cpu":
             self.model_name = os.getenv("WHISPER_MODEL", "large-v3") # Was "medium"
             self.compute_type = "int8"
        else:
             self.model_name = os.getenv("WHISPER_MODEL", "large-v3")
             self.compute_type = "float16"
             
        self.batch_size = 4 

    async def process_job(self, job_id: str):
        """
        Main entry point for embedded background processing of a job via WhisperX.
        Includes Transcription -> Alignment -> Diarization.
        """
        logger.info(f"Starting processing for job {job_id}")
        
        # 1. Fetch Job
        job = await db.get_db().jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        # 1. Update Status to Processing with initial progress
        await db.get_db().jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {
                "status": JobStatus.PROCESSING,
                "started_at": datetime.utcnow(),
                "status_message": "Initializing...",
                "progress": 1
            }}
        )

        temp_audio_path = None
        try:
            # 2. Decrypt Audio File
            encrypted_file_key = job.get("file_key")
            if not encrypted_file_key:
                raise ValueError("Encyption key (file_key) is missing. This recording might be from an older version and cannot be recovered. Please delete it and upload again.")
                
            file_key = decode_str(encrypted_file_key)
            
            file_path = job["file_path"]
            with open(file_path, "rb") as f:
                encrypted_content = f.read()
            
            audio_data = decrypt_data(encrypted_content, file_key)
            
            # Write decrypted audio to temp file for WhisperX
            # (whisperx.load_audio needs a file path usually)
            ext = "wav"
            if job.get('original_filename'):
                ext = job['original_filename'].split('.')[-1]
            elif job.get('filename'):
                ext = job['filename'].split('.')[-1]
                
            temp_audio_path = f"/tmp/{job_id}_temp.{ext}"
            with open(temp_audio_path, "wb") as f:
                 f.write(audio_data)

            # 3. Optimize Execution Config & Load Config
            config = job.get("config", {})
            model_name = os.getenv("WHISPER_MODEL", "large-v3") # Default to large-v3 as properly set now
            
            logger.info(f"Loading WhisperX model: {model_name} on {self.device} ({self.compute_type})")
            
            result = {}
            segments = []
            
            # CHECK FOR HIDOCK MODE (Transcript File provided)
            # If transcript_file_path is present, we skip ASR.
            transcript_file_path = job.get("transcript_file_path")
            
            if transcript_file_path and os.path.exists(transcript_file_path):
                 await self.update_progress(job_id, "HiDock Mode: Skipping ASR. Loading Transcript...", 10)
                 
                 # Decrypt/Read transcript file
                 # Access key again just in case (we have file_key)
                 try:
                     with open(transcript_file_path, "rb") as tf:
                         enc_trans_content = tf.read()
                     # Try decrypting. If user uploaded plain text (via API not encrypting?) 
                     # we assume API encrypts EVERYTHING.
                     trans_bytes = decrypt_data(enc_trans_content, file_key)
                     trans_text = trans_bytes.decode('utf-8')
                 except Exception:
                     # Fallback if not encrypted (dev testing?)
                     with open(transcript_file_path, "r", encoding="utf-8") as tf:
                         trans_text = tf.read()

                 if transcript_file_path.endswith(".srt"):
                     # Parse SRT
                     import re
                     # Simple SRT parser
                     pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:(?!\d+\n\d{2}:\d{2}:\d{2},\d{3}).)*?)\n\n', re.DOTALL)
                     matches = pattern.findall(trans_text + "\n\n")
                     
                     def parse_time(t_str):
                         h, m, s_ms = t_str.split(':')
                         s, ms = s_ms.split(',')
                         return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000.0

                     segments = []
                     for m in matches:
                         start = parse_time(m[1])
                         end = parse_time(m[2])
                         text_content = m[3].replace('\n', ' ').strip()
                         segments.append({"start": start, "end": end, "text": text_content})
                         
                 else:
                     # Assume TXT - Split by sentences
                     import re
                     sentences = re.split(r'(?<=[.!?])\s+', trans_text)
                     segments = [{"text": s.strip(), "start": 0.0, "end": 0.0} for s in sentences if s.strip()]

                 result = {"segments": segments, "language": job.get("language", "en")}

            # CHECK FOR LEGACY ALIGNMENT MODE (Text provided in DB field)
            elif job.get("transcript_text"):
                await self.update_progress(job_id, "Skipping Transcription (Text provided). Preparing for Alignment...", 10)
                text = job["transcript_text"]
                import re
                sentences = re.split(r'(?<=[.!?])\s+', text)
                segments = [{"text": s.strip(), "start": 0.0, "end": 0.0} for s in sentences if s.strip()]
                result = {"segments": segments, "language": job.get("language", "en")} 
            
            else:
                # 4. Transcribe (ASR)
                await self.update_progress(job_id, f"Transcribing with {model_name}...", 5)
                # Load model with specific VAD settings if possible (WhisperX load_model has limited params)
                # We apply VAD settings during Diarization mostly, but ASR has vad_filter too.
                vad_options = {
                    "vad_onset": config.get("vad_onset", 0.5),
                    "vad_offset": config.get("vad_offset", 0.363)
                }
                
                model = whisperx.load_model(
                    model_name, 
                    self.device, 
                    compute_type=self.compute_type, 
                    download_root=settings.TRANSCRIPT_STORAGE_PATH,
                    # Injecting VAD options into load_model if supported? 
                    # WhisperX load_model signature: (..., vad_options=None, ...)
                    vad_options=vad_options
                )
                
                audio = whisperx.load_audio(temp_audio_path)
                
                # Update progress before heavy work
                await self.update_progress(job_id, "Transcribing audio (this may take a while)...", 20)
                result = model.transcribe(audio, batch_size=self.batch_size)
                
                # Free ASR model
                del model
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            
            # 4. Alignment (Optional phase)
            try:
                await self.update_progress(job_id, "Aligning text...", 60)
                audio = whisperx.load_audio(temp_audio_path) # Reload usually fast or cached?
                logger.info(f"Loading alignment model for language {result['language']}...")
                model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=self.device)
                
                if model_a is not None:
                    logger.info("Performing alignment...")
                    result = whisperx.align(result["segments"], model_a, metadata, audio, self.device, return_char_alignments=False)
                    # Free alignment model
                    del model_a
                    gc.collect()
                    if self.device == "cuda":
                        torch.cuda.empty_cache()
                else:
                    logger.warning(f"whisperx.load_align_model returned None for {result['language']}. Skipping.")
            except Exception as align_error:
                import traceback
                logger.warning(f"Alignment phase failed for job {job_id}: {align_error}")
                # We save the align error but continue to allow the job to finish with basic transcription
                await db.get_db().jobs.update_one(
                    {"_id": ObjectId(job_id)},
                    {"$set": {"status_message": f"Alignment skipped due to error: {str(align_error)}"}}
                )

            # 5. Diarization (Optional phase)
            # Check if HF_TOKEN is present
            if settings.HF_TOKEN:
                try:
                    await self.update_progress(job_id, "Diarizing speakers (Loading model)...", 80)
                    diarize_model = whisperx.diarize.DiarizationPipeline(use_auth_token=settings.HF_TOKEN, device=self.device)
                    
                    await self.update_progress(job_id, "Diarizing speakers (Processing)...", 90)
                    
                    # Ensure audio is loaded (if ASR/Align skipped or failed)
                    if 'audio' not in locals():
                         audio = whisperx.load_audio(temp_audio_path)
                    
                    min_speakers = config.get("min_speakers")
                    max_speakers = config.get("max_speakers")
                    
                    diarize_segments = diarize_model(audio, min_speakers=min_speakers, max_speakers=max_speakers)
                    
                    result = whisperx.assign_word_speakers(diarize_segments, result)
                    
                    # Free diarize model
                    del diarize_model
                    gc.collect()
                    if self.device == "cuda":
                        torch.cuda.empty_cache()
                except Exception as diarize_error:
                    logger.warning(f"Diarization phase failed for job {job_id}: {diarize_error}")
                    await db.get_db().jobs.update_one(
                        {"_id": ObjectId(job_id)},
                        {"$set": {"status_message": f"Diarization skipped. This usually happens if the HF_TOKEN is invalid or models haven't been accepted on HuggingFace: {str(diarize_error)}"}}
                    )
            else:
                logger.warning("HF_TOKEN not found, skipping diarization")

            # 7. Encrypt Result
            await self.update_progress(job_id, "Finalizing...", 95)
            result_json = json.dumps(result).encode('utf-8')
            encrypted_transcript = encrypt_data(result_json, file_key)
            
            transcript_filename = f"{job['filename']}.json.enc"
            transcript_path = os.path.join(os.path.dirname(file_path), transcript_filename)
            
            with open(transcript_path, "wb") as f:
                f.write(encrypted_transcript)
                
            # 8. Update Job
            # Calculate duration
            # WhisperX result doesn't always have global duration, we can get it from segments
            duration = 0
            if result.get("segments"):
                 duration = result["segments"][-1]["end"]
            
            await db.get_db().jobs.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": {
                    "status": JobStatus.COMPLETED,
                    "status_message": "Completed", # Clear message
                    "progress": 100,
                    "completed_at": datetime.utcnow(),
                    "transcript_path": transcript_path,
                    "duration": duration
                }}
            )
            logger.info(f"Job {job_id} completed successfully")

        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.exception(f"Error processing job {job_id}: {e}")
            await db.get_db().jobs.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": {
                    "status": JobStatus.FAILED,
                    "status_message": f"Failed: {str(e)}\n{error_traceback}",
                    "progress": 0
                }}
            )
        finally:
            # Cleanup temp file
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)

    def log_progress(self, job_id, status_msg, percent=None):
        # This is a synchronous log for internal use, update_progress handles DB
        if percent is not None:
            logger.info(f"Job {job_id}: {status_msg} ({percent}%)")
        else:
            logger.info(f"Job {job_id}: {status_msg}")

    async def update_progress(self, job_id, message, percent=None):
        # This updates the database
        update_data = {"status_message": message}
        if percent is not None:
            update_data["progress"] = percent
            
        await db.get_db().jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": update_data}
        )

    async def process_diarization_only(self, job_id: str):
        """
        Runs ONLY the diarization phase on an existing COMPLETED job with a transcript.
        """
        logger.info(f"Starting standalone diarization for job {job_id}")
        
        job = await db.get_db().jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        temp_audio_path = None
        try:
            # 1. Decrypt Audio
            encrypted_file_key = job.get("file_key")
            file_key = decode_str(encrypted_file_key)
            file_path = job["file_path"]
            
            with open(file_path, "rb") as f:
                encrypted_content = f.read()
            audio_data = decrypt_data(encrypted_content, file_key)

            ext = "wav"
            if job.get('original_filename'):
                ext = job['original_filename'].split('.')[-1]
            elif job.get('filename'):
                ext = job['filename'].split('.')[-1]

            temp_audio_path = f"/tmp/{job_id}_diarize.{ext}"
            with open(temp_audio_path, "wb") as f:
                 f.write(audio_data)

            # 2. Decrypt Transcript (to get segments)
            transcript_path = job["transcript_path"]
            with open(transcript_path, "rb") as f:
                tr_enc = f.read()
            tr_dec = decrypt_data(tr_enc, file_key)
            result = json.loads(tr_dec.decode('utf-8'))

            # 3. Load Audio for WhisperX
            audio = whisperx.load_audio(temp_audio_path)
            
            # 4. Run Diarization
            if not settings.HF_TOKEN:
                 raise ValueError("HF_TOKEN is missing in server configuration.")
                 
            await self.update_progress(job_id, "Diarizing (Loading model)...")
            
            # Capture standard output/error to catch Pyannote's print statements on failure
            import io
            import sys
            from contextlib import redirect_stdout, redirect_stderr
            
            capture_stream = io.StringIO()
            diarize_model = None
            
            try:
                with redirect_stdout(capture_stream), redirect_stderr(capture_stream):
                    diarize_model = whisperx.diarize.DiarizationPipeline(use_auth_token=settings.HF_TOKEN, device=self.device)
            except Exception as e:
                # Fallback if wrapper fails
                logger.error(f"Diarization init crashed: {e}")

            captured_output = capture_stream.getvalue()
            
            if diarize_model is None:
                 logger.error(f"DiarizationPipeline returned None. Output: {captured_output}")
                 
                 error_details = "Unknown Error"
                 if "Accept the user conditions" in captured_output:
                     error_details = "You must accept the user agreement on HuggingFace for 'pyannote/speaker-diarization-3.1' AND 'pyannote/segmentation-3.0'."
                 elif "Login required" in captured_output or "Unauthorized" in captured_output:
                      error_details = "Invalid HF_TOKEN. Please check your token permissions."
                 elif "private or gated" in captured_output:
                      error_details = "Access Denied: This model is GATED. You MUST visit https://hf.co/pyannote/speaker-diarization-3.1 and https://hf.co/pyannote/segmentation-3.0 to accept the User Agreements."
                 
                 if "visit https://hf.co" in captured_output:
                     # Extract link roughly? Or just give generic advice.
                     pass

                 raise ValueError(f"Model Init Failed. {error_details} Raw output: {captured_output[:300]}")

            await self.update_progress(job_id, "Diarizing (Processing)...")
            diarize_segments = diarize_model(audio)
            
            # 5. Assign Speakers
            result = whisperx.assign_word_speakers(diarize_segments, result)
            
            # Free memory
            del diarize_model
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
                
            # 6. Save Updated Transcript
            result_json = json.dumps(result).encode('utf-8')
            encrypted_transcript = encrypt_data(result_json, file_key)
            with open(transcript_path, "wb") as f:
                f.write(encrypted_transcript)
                
            await db.get_db().jobs.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": {
                    "status_message": "Diarization Completed", 
                    "status": JobStatus.COMPLETED # Ensure it stays completed
                }}
            )
            logger.info(f"Diarization only completed for {job_id}")

        except Exception as e:
            import traceback
            err = traceback.format_exc()
            logger.error(f"Diarization only failed: {e}\n{err}")
            await db.get_db().jobs.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": {"status_message": f"Diarization Failed: {str(e)}"}}
            )
        finally:
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)


transcription_service = TranscriptionService()
