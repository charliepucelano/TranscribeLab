
import os
import aiohttp
import logging
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

async def generate_summary(transcript_text: str, meeting_type: str = "General Meeting", language: str = "en", model: str = "qwen2.5:32b") -> str:
    """
    Generates a summary using Ollama with the "Signs of AI" style guide AND meeting template injected.
    """
    style_guide = await get_style_guide()
    template = get_template(meeting_type, language)
    
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

    system_prompt = (
        f"{role_instruction}\n"
        f"MEETING TYPE: {template.name}\n"
        f"{template.system_instruction}\n\n"
        f"{style_header}\n"
        f"{style_guide}\n\n"
        f"{structure_header}\n"
        f"{template.output_structure}\n\n"
        f"{no_fluff_instruction}\n"
        "Format with Markdown headers."
    )
    
    user_prompt = f"TRANSCRIPT:\n{transcript_text}\n\nINSTRUCTION: Summarize the above transcript following the structure and style guide strictly."
    if language == "es":
        user_prompt = f"TRANSCRIPCIÓN:\n{transcript_text}\n\nINSTRUCCIÓN: Resume la transcripción anterior siguiendo estrictamente la estructura y la guía de estilo."

    payload = {
        "model": model,
        "prompt": user_prompt,
        "system": system_prompt,
        "stream": False
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{ollama_url}/api/generate", json=payload) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(f"Ollama Error ({resp.status}): {error_text}")
                    return "Error: Could not generate summary. AI Service unavailable."
                
                data = await resp.json()
                return data.get("response", "No response from AI.")
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        return f"Error: Summarization failed. {str(e)}"
