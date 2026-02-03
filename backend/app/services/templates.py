
from typing import Dict

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
## Executive Summary
[Brief overview]

## Key Discussion Points
- [Point 1]
- [Point 2]

## Action Items
- [User]: [Task]
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
## Resumen Ejecutivo
[Breve descripción]

## Puntos Clave de Discusión
- [Punto 1]
- [Punto 2]

## Elementos de Acción (Tareas)
- [Usuario]: [Tarea]
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

def get_template(meeting_type: str, language: str = "en") -> MeetingTemplate:
    # Default to English if language not found
    lang_templates = TEMPLATES.get(language, TEMPLATES["en"])
    # Default to General Meeting if type not found in language
    return lang_templates.get(meeting_type, lang_templates["General Meeting"])
