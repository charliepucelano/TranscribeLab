# TranscribeLab — AI Lessons Learned

> A retrospective on what we learned building a self-hosted, privacy-first, AI-powered meeting transcription platform — from architecture decisions to model selection, prompt engineering, and the hard lessons that only come from running ML models on real hardware.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Evolution: From Microservice to Embedded AI](#2-architecture-evolution-from-microservice-to-embedded-ai)
3. [The AMD / CPU Problem](#3-the-amd--cpu-problem)
4. [Model Selection Journey](#4-model-selection-journey)
5. [Prompt Engineering: The Anti-AI Style Guide](#5-prompt-engineering-the-anti-ai-style-guide)
6. [Warming Up the Model — Reasoning vs. Unclear Instructions](#6-warming-up-the-model--reasoning-vs-unclear-instructions)
7. [PyTorch Pitfalls — Segfaults, Weights, and Process Isolation](#7-pytorch-pitfalls--segfaults-weights-and-process-isolation)
8. [Speaker Diarization — The Hidden Complexity](#8-speaker-diarization--the-hidden-complexity)
9. [HiDock Mode — When the AI Pipeline is Too Slow](#9-hidock-mode--when-the-ai-pipeline-is-too-slow)
10. [Summarization: Timeouts, Fallbacks, and Model Cascading](#10-summarization-timeouts-fallbacks-and-model-cascading)
11. [Real-Time Progress: SSE for Long-Running AI Tasks](#11-real-time-progress-sse-for-long-running-ai-tasks)
12. [Performance Optimization: Interval Trees for Speaker Assignment](#12-performance-optimization-interval-trees-for-speaker-assignment)
13. [Key Takeaways](#13-key-takeaways)

---

## 1. Project Overview

**TranscribeLab** is a self-hosted platform that transcribes meeting audio and generates structured summaries. It combines two distinct AI systems:

| Component | Purpose | Model |
|---|---|---|
| **WhisperX** | Speech-to-Text (ASR) + Alignment + Speaker Diarization | `whisper-large-v3` + `pyannote/speaker-diarization-3.1` |
| **Ollama** | Meeting Summarization via LLM | `qwen2.5:32b` → `qwen3:32b` |

All processing runs locally — no external cloud APIs — with encrypted audio at rest (AES-GCM). This constraint (privacy + local hardware) shaped every AI decision we made.

---

## 2. Architecture Evolution: From Microservice to Embedded AI

### v1.0 — The Microservice Approach (Feb 2026)

The initial architecture used a **separate Docker container** running `fedirz/faster-whisper-server` (an OpenAI-compatible Whisper API), and the backend called it over HTTP:

```
┌─────────────┐     HTTP      ┌──────────────────────┐
│   Backend   │ ───────────→  │  WhisperX Container  │
│  (FastAPI)  │   /v1/audio   │  (faster-whisper-server) │
└─────────────┘               └──────────────────────┘
```

```python
# v1.0 — External API call
async with httpx.AsyncClient(timeout=1200.0) as client:
    response = await client.post(self.whisper_url, files=files, data=data)
```

**Problems:**
- The `faster-whisper-server` image only did basic ASR — **no diarization** (who said what).
- The OpenAI-compatible endpoint didn't support WhisperX's alignment or speaker assignment features.
- Sending large audio files over HTTP inside Docker was slow and memory-wasteful (audio had to be fully buffered).

### v2.0 — Embedded In-Process AI (Feb 2026, same week)

We **eliminated the WhisperX container entirely** and loaded models directly inside the FastAPI backend:

```
┌──────────────────────────────────────┐
│           Backend (FastAPI)          │
│                                      │
│  ┌──────────┐  ┌──────────┐         │
│  │ WhisperX │  │ Pyannote │         │
│  │  (ASR)   │  │ (Diarize)│         │
│  └──────────┘  └──────────┘         │
│                                      │
│  Alignment → Diarization → Encrypt  │
└──────────────────────────────────────┘
         │
         │ HTTP (host network)
         ▼
┌──────────────────┐
│  Ollama (Host)   │
│  qwen2.5:32b     │
└──────────────────┘
```

```python
# v2.0 — Direct in-process model loading
model = whisperx.load_model("large-v3", self.device, compute_type="int8")
result = model.transcribe(audio, batch_size=4)
```

**Lesson:** For privacy-first applications where you control the hardware, embedding ML models directly in your application process gives you far more control over the pipeline (alignment, diarization, VAD tuning) than relying on third-party API wrappers. The trade-off is that your backend becomes a heavyweight process (16–48 GB RAM).

---

## 3. The AMD / CPU Problem

### The Hardware Reality

The development machine ran an **AMD Ryzen AI** processor — no NVIDIA GPU. This single constraint cascaded into dozens of engineering decisions:

```python
self.device = "cuda" if torch.cuda.is_available() else "cpu"

if self.device == "cpu":
    self.model_name = "large-v3"
    self.compute_type = "int8"    # ← Forced: float16 not available on CPU
else:
    self.model_name = "large-v3"
    self.compute_type = "float16"
```

### What We Learned

| Issue | NVIDIA GPU | AMD CPU (our case) |
|---|---|---|
| Compute type | `float16` (native) | `int8` only (quantized) |
| Whisper `large-v3` speed | ~2-5 min for 1h audio | ~15-40 min for 1h audio |
| Alignment (Wav2Vec2) | Stable | **Segfaults** on long files |
| Diarization (Pyannote) | ~2 min | ~5-10 min |
| Memory footprint | GPU VRAM (separate) | Shared system RAM: **16–48 GB** |

### The Docker Memory Configuration

We had to explicitly reserve large amounts of RAM in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 48G
    reservations:
      memory: 16G
```

**Lesson:** If you're building an AI product, assume NVIDIA CUDA from day one unless you want to spend significant engineering time on CPU fallbacks. AMD ROCm support for PyTorch is improving but isn't production-ready for the models we needed (WhisperX, Pyannote). The `int8` quantization on CPU is functional but 5–10x slower.

---

## 4. Model Selection Journey

### Whisper Models

| Phase | Model | Why |
|---|---|---|
| v1.0 initial | `medium` (env default) | Fast, lower accuracy |
| v1.0 quick change | `large-v3` | User demanded better accuracy — worth the speed trade |

The config evolved to allow runtime override:
```python
self.model_name = os.getenv("WHISPER_MODEL", "large-v3")  # Was "medium"
```

**Lesson:** Start with the best model you can afford to run. Users care about accuracy more than speed for transcription — a 15-minute wait is acceptable if the output is correct. A 2-minute wait with garbage results is not.

### LLM Models for Summarization

| Phase | Model | Context Window | Notes |
|---|---|---|---|
| v1.0 | `qwen2.5:32b` | 8K default | Good quality, but context was too small for long meetings |
| v2.0 | `qwen2.5:32b` | **32K** (explicit) | Set `num_ctx: 32768` — fixed truncation issues |
| Current Modelfile | `qwen3.5:122b-a10b` | 32K | Exploring larger MoE models for better quality |

```python
# Explicit context window — critical for meeting transcripts
payload = {
    "model": current_model,
    "prompt": user_prompt,
    "system": system_prompt,
    "stream": False,
    "options": {
        "num_ctx": 32768  # ← This was missing in v1.0!
    }
}
```

**Lesson:** The default context window for most local LLM models (often 2K–8K tokens) is silently too small for meeting transcripts. A 1-hour meeting can easily produce 10K–20K tokens. When the context overflows, the model doesn't error — it just silently truncates the input and produces a summary of only the first few minutes. **Always set `num_ctx` explicitly.**

---

## 5. Prompt Engineering: The Anti-AI Style Guide

### The Problem: LLM Summaries Sound Like LLMs

Early summaries from `qwen2.5:32b` were immediately recognizable as AI-generated. They used words like "delve", "tapestry", "seamlessly", and opened with "In this meeting, the speakers discussed..."

### The Solution: Wikipedia's "Signs of AI Writing"

We saved the actual [Wikipedia article on detecting AI-generated text](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) and used it as a **negative style guide** — telling the model what NOT to do:

```
# Wikipedia: Signs of AI Writing - Style Guide
# This guide is used to instruct the AI to AVOID these patterns.

## Content Red Flags (AVOID)
- "It is important to note...", "This represents a significant shift..."
- Superficial Analysis: broad, shallow statements that sound authoritative
- Vague Attributions: "Critics argue...", "Some say..."
- Promotional Language: "Cutting-edge", "State-of-the-art", "Seamlessly"

## Language Red Flags (AVOID)
- "The Tapestry" Words: delve, tapestry, landscape, realm, dynamic, testament
- Negative Parallelisms: "Not only X, but also Y."
- The "Rule of Three" (excessive X, Y, and Z lists)

## Desired Style (ADOPT)
- Neutral Point of View (NPOV): stating facts without editorializing.
- Direct & Concise: "is" and "are" instead of "serves as" or "functions as".
- No Fluff: Remove "It is worth noting that", "Interestingly", "Crucially".
```

This guide is loaded from a file and **injected into every summarization prompt** as `CRITICAL STYLE INSTRUCTIONS (DO NOT IGNORE)`.

**Lesson:** The best way to fight AI-sounding output isn't to say "write naturally." It's to give the model a concrete **blacklist** of patterns to avoid, drawn from real-world observations of AI writing. The Wikipedia community's work on identifying AI patterns is an excellent, freely available resource for this.

---

## 6. Warming Up the Model — Reasoning vs. Unclear Instructions

### The Context Problem

Summarization quality varied wildly depending on how much context the model received. Without explicit metadata, the model would:

- Guess the meeting date (often wrong)
- Hallucinate participant names from vague transcript references
- Miss the meeting type (standup vs. interview vs. client call)

### The Template + Context System

We built a **template injection system** that combines meeting-type-specific structure with user-provided metadata:

```python
system_prompt = (
    f"{role_instruction}\n"
    f"MEETING TYPE: {template.name}\n"
    f"MANDATORY METADATA FROM USER:\n{context_str}\n"  # ← Date, Participants, Notes
    f"{template.system_instruction}\n\n"
    f"{style_header}\n"
    f"{style_guide}\n\n"
    f"{structure_header}\n"
    f"{template.output_structure}\n\n"  # ← Exact Markdown structure to follow
    f"{no_fluff_instruction}\n"
    "CRITICAL INSTRUCTION: If 'USER PROVIDED DATE' or 'USER PROVIDED PARTICIPANTS' "
    "are present above, you MUST use them exactly as written."
)
```

The templates provide **exact output structure** with Markdown formatting:

```markdown
## 🎯 Executive Summary
[Concise high-level overview]

## 🔑 Key Decisions
- [Decision 1]

## ✅ Action Items
| Owner | Task | Deadline |
|-------|------|----------|
```

### What "Warming Up" Means in Practice

When a reasoning model (like Qwen 3 with its `<think>` mode) receives unclear instructions, it spends its "thinking budget" trying to figure out **what** to do rather than **doing** it well. By providing:

1. **Explicit role** ("You are an expert meeting secretary")
2. **Explicit structure** (the exact Markdown template)
3. **Explicit constraints** (the style guide blacklist)
4. **Explicit context** (date, participants, notes injected by the user)

...the model's reasoning focuses on content quality rather than format guessing.

**Lesson:** With local LLMs, the quality of the prompt structure matters even more than with cloud APIs (GPT-4, Claude). Cloud models have been RLHF'd extensively on "figure out what the user wants." Local models need you to be explicit. A structured system prompt with concrete examples and negative constraints consistently outperforms a vague "summarize this meeting."

---

## 7. PyTorch Pitfalls — Segfaults, Weights, and Process Isolation

### The `weights_only` Breaking Change

PyTorch 2.6+ changed the default behavior of `torch.load()` to require `weights_only=True`, breaking WhisperX model loading. We needed a **triple bypass**:

```python
# 1. Monkey-patch torch.load globally
original_torch_load = torch.load
def patched_torch_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return original_torch_load(*args, **kwargs)
torch.load = patched_torch_load

# 2. Register OmegaConf classes as safe globals
torch.serialization.add_safe_globals([
    omegaconf.listconfig.ListConfig,
    omegaconf.dictconfig.DictConfig,
    omegaconf.base.ContainerMetadata,
    omegaconf.base.Metadata
])

# 3. Environment variable fallback
os.environ["TORCH_SKIP_WEIGHTS_ONLY_CHECK"] = "1"
```

**Lesson:** AI dependencies are a minefield of breaking changes. Pin your PyTorch version. If you can't, understand that `torch.load` security changes will break every model that uses pickle-based weights (which is most of them). The triple-bypass approach is ugly but necessary when you don't control the upstream model format.

### Alignment Segfaults on CPU

The WhisperX alignment step (which uses Facebook's Wav2Vec2) would **segfault** (not throw a Python exception — a C-level crash) on long audio files when running on CPU. This killed the entire backend process.

**Solution:** We isolated alignment in a **separate process** using `ProcessPoolExecutor`:

```python
# Running alignment in a child process to survive segfaults
with concurrent.futures.ProcessPoolExecutor(max_workers=1) as pool:
    try:
        aligned_result = await loop.run_in_executor(pool, align_func)
    except concurrent.futures.process.BrokenProcessPool as bp_err:
        logger.error(f"Alignment crashed via Segfault/OOM: {bp_err}")
        # Continue without alignment — transcript still usable
```

**Lesson:** When running ML models on CPU, prepare for C-level crashes that bypass Python's exception handling. Process isolation (not thread isolation) is the only reliable protection. Design your pipeline so each stage can fail independently without losing the work from previous stages.

---

## 8. Speaker Diarization — The Hidden Complexity

### Gated Models and HuggingFace Agreements

Pyannote's diarization models are **gated** on HuggingFace. Even with a valid `HF_TOKEN`, users must manually visit two URLs and accept license agreements:

- `https://hf.co/pyannote/speaker-diarization-3.1`
- `https://hf.co/pyannote/segmentation-3.0`

The model doesn't throw a clear error — it prints to stdout and returns `None`. We had to capture stdout/stderr to detect the actual failure:

```python
capture_stream = io.StringIO()
with redirect_stdout(capture_stream), redirect_stderr(capture_stream):
    diarize_model = whisperx.diarize.DiarizationPipeline(
        use_auth_token=settings.HF_TOKEN, device=self.device
    )

captured_output = capture_stream.getvalue()
if "Accept the user conditions" in captured_output:
    error_details = "You must accept the user agreement on HuggingFace..."
elif "private or gated" in captured_output:
    error_details = "Access Denied: This model is GATED..."
```

### VAD Tuning

Voice Activity Detection (VAD) settings dramatically affect diarization quality:

```python
vad_options = {
    "vad_onset": config.get("vad_onset", 0.5),   # Default 0.5
    "vad_offset": config.get("vad_offset", 0.363)
}
```

- **Noisy environments** → increase `vad_onset` to 0.6+
- **Quiet/clear audio** → default 0.4–0.5 works fine
- **Min/Max speakers** → set explicitly to prevent hallucinated speakers

**Lesson:** Diarization is the most fragile part of any speech pipeline. It fails silently (models return `None` instead of raising), requires manual license acceptance on third-party platforms, and its quality is highly sensitive to audio conditions. Build your pipeline to gracefully degrade — a transcript without speaker labels is still useful.

---

## 9. HiDock Mode — When the AI Pipeline is Too Slow

### The Insight

Many users already had transcripts from tools like **HiDock** (macOS app) or existing `.srt` files. Running full ASR on their audio was wasteful when they just needed alignment + diarization.

### The Solution

We added a "HiDock Mode" that **parses existing transcripts** and skips the ASR step entirely:

```python
# Parse HiDock TXT format:
# "00:02:39 - 00:03:41 Unknown Speaker:\n\nText content here..."
hidock_pattern = re.compile(
    r'(\d{2}:\d{2}:\d{2})\s*-\s*(\d{2}:\d{2}:\d{2})(?:\s+([^:]+?):)?\s*\n(.*?)(?=\n\d{2}:\d{2}:\d{2}\s*-|\Z)',
    re.DOTALL
)
```

This made processing **3–5x faster** because:
1. No ASR model loading (~30s saved)
2. No transcription (~15-40 min saved for 1h audio)
3. Alignment + Diarization on pre-segmented text is much cheaper

**Lesson:** Not every user needs the full AI pipeline. Offering a "bypass" mode where users bring their own transcript (from any tool) dramatically improves UX for power users and reduces server load. The key is making the parser flexible enough to handle multiple transcript formats.

---

## 10. Summarization: Timeouts, Fallbacks, and Model Cascading

### The Timeout Problem

A 32B parameter model summarizing a 1-hour meeting transcript can take **5–30 minutes on CPU**. The original code had no timeout, causing the frontend to show an infinite spinner.

**Solution:** We set an explicit 2-hour timeout and moved summarization to a background task with SSE progress:

```python
OLLAMA_TIMEOUT: int = 7200  # 2 hours — yes, it can take that long on CPU

timeout = aiohttp.ClientTimeout(total=settings.OLLAMA_TIMEOUT)
async with aiohttp.ClientSession(timeout=timeout) as session:
    async with session.post(f"{ollama_url}/api/generate", json=payload) as resp:
        ...
```

### Model Cascading / Fallback

If the primary model fails (OOM, not loaded, network error), we automatically try a fallback:

```python
models_to_try = [model]
if model != "qwen3:32b":
    models_to_try.append("qwen3:32b")  # Fallback model

for current_model in models_to_try:
    try:
        # ... attempt summarization
        return summary_text + metadata
    except Exception as e:
        last_error = error_msg
        continue  # Try next model

# If all models failed
return f"Error: Could not generate summary. Details: {last_error}"
```

**Lesson:** Local LLM inference is unreliable compared to cloud APIs. Models crash, run out of memory, or simply aren't loaded. Always implement:
1. **Explicit timeouts** (generous ones — CPU inference is slow)
2. **Model fallback chains** (try model A → try model B → return error)
3. **Background processing** (never block the HTTP request)

---

## 11. Real-Time Progress: SSE for Long-Running AI Tasks

### The Problem

ASR can take 15–40 minutes. Users staring at a loading spinner for that long will close the tab, assuming it's broken.

### The Solution: Server-Sent Events (SSE)

We implemented a polling-based SSE endpoint that streams progress updates to the frontend:

```
Client ←── SSE ──── Backend ←── DB (polled every 1s)
                         ↑
                    Background Task
                    (updates progress
                     to MongoDB)
```

The background task updates progress at each pipeline stage:
```python
await self.update_progress(job_id, "Transcribing with large-v3...", 5)
# ... transcription ...
await self.update_progress(job_id, "Aligning text...", 60)
# ... alignment ...
await self.update_progress(job_id, "Diarizing speakers...", 80)
# ... diarization ...
await self.update_progress(job_id, "Finalizing...", 95)
```

**Lesson:** Any AI pipeline that takes more than ~10 seconds needs real-time progress feedback. SSE is simpler than WebSockets for this use case — the data only flows in one direction (server → client). Polling the database every 1 second is "wasteful" in theory, but in practice it's negligible compared to the cost of running ML models.

---

## 12. Performance Optimization: Interval Trees for Speaker Assignment

### The Original Problem

WhisperX's default speaker assignment uses **O(n×m) linear scans** — for every transcript segment, it checks every diarization segment for overlap. For long podcasts (3+ hours, ~10K segments × ~5K diarization segments), this took minutes.

### The Solution: Custom Interval Tree

We replaced the linear scan with a sorted-array interval tree using binary search:

```python
class IntervalTree:
    """O(log n) overlap queries instead of O(n) linear scan.
    Achieves ~228x speedup for 3+ hour content."""

    def __init__(self, intervals):
        sorted_intervals = sorted(intervals, key=lambda x: x[0])
        self.starts = np.array([i[0] for i in sorted_intervals])
        self.ends = np.array([i[1] for i in sorted_intervals])
        self.speakers = [i[2] for i in sorted_intervals]

    def query(self, start, end):
        right_idx = np.searchsorted(self.starts, end, side='left')
        candidates = slice(0, right_idx)
        overlaps = (self.starts[candidates] < end) & (self.ends[candidates] > start)
        # ... compute intersection durations
```

**Result:** ~228x speedup for speaker assignment on long-form content.

**Lesson:** Even in an AI-heavy application, classical algorithms matter. The ML models are the bottleneck for most steps, but the **post-processing** (matching speakers to words) was accidentally quadratic. Profiling the non-ML parts of your pipeline can yield massive wins.

---

## 13. Key Takeaways

### Architecture

| Lesson | Details |
|---|---|
| **Embed models when you control hardware** | Microservice Whisper containers add overhead without giving you pipeline control |
| **Design for graceful degradation** | Each AI stage (ASR → Alignment → Diarization → Summary) should fail independently |
| **Background everything** | Never run ML inference in an HTTP request handler |

### Models & Hardware

| Lesson | Details |
|---|---|
| **Assume NVIDIA CUDA** | AMD CPU fallback is possible but costs 5–10x speed and introduces segfault risks |
| **Pin your PyTorch version** | Breaking changes in `torch.load` will break model loading with no warning |
| **Set `num_ctx` explicitly** | Silent context truncation is the #1 cause of bad LLM summaries |
| **Offer model fallback chains** | Local models crash; always have a plan B |

### Prompt Engineering

| Lesson | Details |
|---|---|
| **Use negative style guides** | A blacklist of AI-sounding patterns works better than "write naturally" |
| **Provide exact output structure** | Give the model the Markdown template it should fill in |
| **Inject user context as "mandatory metadata"** | Dates, participants, and notes should override anything the model infers |
| **Warm up reasoning with structure** | Models waste their "thinking budget" on format guessing if you don't constrain it |

### Operations

| Lesson | Details |
|---|---|
| **Capture stdout/stderr from ML libraries** | Many failures are printed, not raised |
| **Isolate dangerous operations in child processes** | Segfaults from C extensions kill your server |
| **SSE for progress on anything > 10 seconds** | Users will close the tab if they can't see progress |
| **Profile your non-ML code too** | A quadratic loop in post-processing can be worse than the model itself |

---

*Written as part of the TranscribeLab project retrospective. All code examples are from the actual production codebase.*
