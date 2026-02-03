
from icalendar import Calendar
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

def parse_outlook_invite(file_content: bytes) -> Dict[str, Any]:
    """
    Parses an .ics file content and returns metadata.
    """
    metadata = {
        "subject": None,
        "description": None,
        "date": None,
        "attendees": [],
        "meeting_type": "General Meeting"
    }
    
    try:
        cal = Calendar.from_ical(file_content)
        
        for component in cal.walk():
            if component.name == "VEVENT":
                metadata["subject"] = str(component.get('summary', ''))
                metadata["description"] = str(component.get('description', ''))
                
                # Date
                dtstart = component.get('dtstart')
                if dtstart:
                    metadata["date"] = dtstart.dt.isoformat() if hasattr(dtstart.dt, 'isoformat') else str(dtstart.dt)
                
                # Attendees (Can be a list or single item)
                attendees = component.get('attendee')
                if attendees:
                    if isinstance(attendees, list):
                        metadata["attendees"] = [str(a).replace("mailto:", "") for a in attendees]
                    else:
                        metadata["attendees"] = [str(attendees).replace("mailto:", "")]
                        
                # Simple Heuristic for Meeting Type
                subject_lower = metadata["subject"].lower()
                if "standup" in subject_lower or "daily" in subject_lower:
                    metadata["meeting_type"] = "Team Standup"
                elif "interview" in subject_lower:
                    metadata["meeting_type"] = "Interview"
                elif "client" in subject_lower:
                    metadata["meeting_type"] = "Client Call"
                    
                break # Only parse the first event
                
    except Exception as e:
        logger.error(f"Failed to parse ICS: {e}")
        
    return metadata
