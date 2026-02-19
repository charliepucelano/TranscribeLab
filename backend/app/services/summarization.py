
import os
import aiohttp
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Fallback guide if file missing
DEFAULT_STYLE_GUIDE = "Avoid: weave, delve, tapestry, in conclusion. Be concise."

async def get_style_guide() -> str:
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        guide_path = os.path.join(current_dir, "..", "core", "style_guide.txt")
        if os.path.exists(guide_path):
            with open(guide_path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        logger.warning(f"Could not load style guide: {e}")
    return DEFAULT_STYLE_GUIDE

from app.services.templates import get_template

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:32b")

async def generate_summary(
    transcript_text: str, 
    meeting_type: str = "General Meeting", 
    language: str = "en", 
    model: str = OLLAMA_MODEL, 
    user_id: Optional[str] = None,
    context_date: Optional[str] = None,
    context_participants: Optional[str] = None,
    context_notes: Optional[str] = None
) -> str:
    """
    Generates a summary using Ollama with the "Signs of AI" style guide AND meeting template injected.
    """
    style_guide = await get_style_guide()
    template = await get_template(meeting_type, language, user_id)
    
    ollama_url = settings.OLLAMA_URL
    
    # Adjust system prompt based on language
    role_instruction = "You are an expert meeting secretary. Your goal is to summarize the provided transcript."
    style_header = "CRITICAL STYLE INSTRUCTIONS (DO NOT IGNORE):"
    structure_header = "REQUIRED OUTPUT STRUCTURE:"
    no_fluff_instruction = "Do not use phrases like 'In this meeting', 'The speakers discussed'. Just state the facts."
    
    if language == "es":
        role_instruction = "Eres un experto secretario de actas. Tu objetivo es resumir la transcripción proporcionada."
        style_header = "INSTRUCCIONES DE ESTILO CRÍTICAS (NO IGNORAR):"
        structure_header = "ESTRUCTURA DE SALIDA REQUERIDA:"
        no_fluff_instruction = "No uses frases como 'En esta reunión', 'Los oradores discutieron'. Solo expón los hechos."

    # Build Context String
    context_str = ""
    if context_date:
        context_str += f"USER PROVIDED DATE: {context_date} (You MUST use this date in the summary header, ignoring any date in the transcript)\n"
    if context_participants:
        context_str += f"USER PROVIDED PARTICIPANTS: {context_participants} (You MUST use these participants, ignoring transcript speakers if they differ)\n"
    if context_notes:
        context_str += f"USER NOTES: {context_notes} (Include this information)\n"

    system_prompt = (
        f"{role_instruction}\n"
        f"MEETING TYPE: {template.name}\n"
        f"MANDATORY METADATA FROM USER:\n{context_str}\n"
        f"{template.system_instruction}\n\n"
        f"{style_header}\n"
        f"{style_guide}\n\n"
        f"{structure_header}\n"
        f"{template.output_structure}\n\n"
        f"{no_fluff_instruction}\n"
        "CRITICAL INSTRUCTION: If 'USER PROVIDED DATE' or 'USER PROVIDED PARTICIPANTS' are present above, you MUST use them exactly as written in the output header. Do not infer them from the text if user provided them."
    )
    
    user_prompt = f"TRANSCRIPT:\n{transcript_text}\n\nINSTRUCTION: Summarize the above transcript following the structure and style guide strictly."
    if language == "es":
        user_prompt = f"TRANSCRIPCIÓN:\n{transcript_text}\n\nINSTRUCCIÓN: Resume la transcripción anterior siguiendo estrictamente la estructura y la guía de estilo."

    # Models to try: first the requested one, then the fallback
    models_to_try = [model]
    if model != "llama3.1:latest":
        models_to_try.append("llama3.1:latest")
        
    last_error = None
    
    for current_model in models_to_try:
        try:
            logger.info(f"Generating summary with model: {current_model}")
            payload = {
                "model": current_model,
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": False
            }
            
            timeout = aiohttp.ClientTimeout(total=600) # 10 minutes
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{ollama_url}/api/generate", json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.warning(f"Ollama Error with {current_model} ({resp.status}): {error_text}")
                        last_error = f"Model {current_model} failed: {error_text}"
                        continue # Try next model
                    
                    data = await resp.json()
                    summary_text = data.get("response", "No response from AI.")
                    
                    # Append Metadata
                    metadata = f"\n\n---\n**Summary Details:**\n- Model: {current_model}\n- Template: {template.name} ({language})"
                    return summary_text + metadata
                    
        except Exception as e:
            logger.warning(f"Summarization failed with {current_model}: {e}")
            last_error = str(e)
            continue
            
    # If we get here, all models failed
    logger.error(f"All summarization models failed. Last error: {last_error}")
    return f"Error: Could not generate summary. AI Service unavailable. Details: {last_error}"
