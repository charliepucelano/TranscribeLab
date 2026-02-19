
from typing import Dict, Optional
from app.core.database import db

class MeetingTemplate:
    def __init__(self, name: str, system_instruction: str, output_structure: str):
        self.name = name
        self.system_instruction = system_instruction
        self.output_structure = output_structure

# Nested dictionary: Language -> Meeting Type -> Template
TEMPLATES: Dict[str, Dict[str, MeetingTemplate]] = {
    "en": {
        "General Meeting": MeetingTemplate(
            "General Meeting",
            "Summarize the meeting comprehensively.",
            """
## 🎯 Executive Summary
[Concise high-level overview of the meeting's purpose and outcome]

## 🔑 Key Decisions
- [Decision 1]
- [Decision 2]

## 💡 Key Discussion Points
- [Topic 1]: [Details]
- [Topic 2]: [Details]

## ✅ Action Items
| Owner | Task | Deadline |
|-------|------|----------|
| [Name] | [Task Description] | [Date/ASAP] |
| [Name] | [Task Description] | [Date/ASAP] |

## 🧠 Sentiment & Tone
[Brief observation of the meeting's tone (e.g., Optimistic, Tense, Productive)]
"""
        ),
        "Interview": MeetingTemplate(
            "Interview",
            "This is a job interview or user interview. Focus on the candidate/user's responses, skills, and key insights.",
            """
## Interviewee Profile / Context
[Brief context]

## Key Questions & Answers
- **Q:** [Question topic]
  **A:** [Summary of response]

## Strengths & Weaknesses (if applicable)
- **Pros:** ...
- **Cons:** ...

## Overall Impression
[Summary]
"""
        ),
        "Team Standup": MeetingTemplate(
            "Team Standup",
            "This is a daily standup. Focus on progress, blockers, and next steps.",
            """
## Updates by Person
- **[Person Name]:** [Update]

## Blocker List
- [Blocker 1]

## Next Steps
- [Immediate Action]
"""
        ),
         "Client Call": MeetingTemplate(
            "Client Call",
            "This is a client meeting. Focus on client requirements, feedback, and commitments.",
            """
## Client Context
[Client Name/Project]

## Requirements / Feedback
- [Requirement 1]

## Agreed Actions (Next Steps)
- [We will do X]
- [Client will do Y]
"""
        ),
    },
    "es": {
        "General Meeting": MeetingTemplate(
            "General Meeting",
            "Resume la reunión de manera integral.",
            """
## 🎯 Resumen Ejecutivo
[Visión general concisa del propósito y resultado de la reunión]

## 🔑 Decisiones Clave
- [Decisión 1]
- [Decisión 2]

## 💡 Puntos Clave de Discusión
- [Tema 1]: [Detalles]
- [Tema 2]: [Detalles]

## ✅ Elementos de Acción (Tareas)
| Responsable | Tarea | Fecha Límite |
|-------------|-------|--------------|
| [Nombre] | [Descripción] | [Fecha/ASAP] |
| [Nombre] | [Descripción] | [Fecha/ASAP] |

## 🧠 Sentimiento y Tono
[Breve observación del tono de la reunión (ej. Optimista, Tenso, Productivo)]
"""
        ),
        "Interview": MeetingTemplate(
            "Interview",
            "Esta es una entrevista de trabajo o de usuario. Céntrate en las respuestas, habilidades y conocimientos clave del candidato/usuario.",
            """
## Perfil del Entrevistado / Contexto
[Breve contexto]

## Preguntas y Respuestas Clave
- **P:** [Tema de la pregunta]
  **R:** [Resumen de la respuesta]

## Fortalezas y Debilidades (si aplica)
- **Pros:** ...
- **Contras:** ...

## Impresión General
[Resumen]
"""
        ),
        "Team Standup": MeetingTemplate(
            "Team Standup",
            "Este es un standup diario (reunión de seguimiento). Céntrate en el progreso, los bloqueos y los siguientes pasos.",
            """
## Actualizaciones por Persona
- **[Nombre]:** [Actualización]

## Lista de Bloqueos
- [Bloqueo 1]

## Siguientes Pasos
- [Acción Inmediata]
"""
        ),
         "Client Call": MeetingTemplate(
            "Client Call",
            "Esta es una reunión con clientes. Céntrate en los requisitos del cliente, comentarios y compromisos.",
            """
## Contexto del Cliente
[Nombre del Cliente/Proyecto]

## Requisitos / Comentarios
- [Requisito 1]

## Acciones Acordadas (Siguientes Pasos)
- [Nosotros haremos X]
- [El cliente hará Y]
"""
        ),
    }
}

async def get_template(meeting_type: str, language: str = "en", user_id: Optional[str] = None) -> MeetingTemplate:
    # 1. Try to fetch custom template if user_id is provided
    if user_id:
        try:
            custom_template = await db.get_db().templates.find_one({
                "user_id": user_id,
                "name": meeting_type,
                "language": language
            })
            
            if custom_template:
                return MeetingTemplate(
                    name=custom_template["name"],
                    system_instruction=custom_template["system_instruction"],
                    output_structure="" # Custom templates generally bake structure into system_instruction or description
                )
        except Exception as e:
            print(f"Error fetching custom template: {e}")

    # 2. Fallback to Built-in
    # Default to English if language not found
    lang_templates = TEMPLATES.get(language, TEMPLATES["en"])
    # Default to General Meeting if type not found in language
    return lang_templates.get(meeting_type, lang_templates["General Meeting"])
