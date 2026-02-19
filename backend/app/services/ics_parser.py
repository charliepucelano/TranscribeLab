from icalendar import Calendar
from datetime import datetime
from typing import List, Optional, Dict, Any
import io

def parse_ics_data(file_content: bytes) -> Dict[str, Any]:
    try:
        cal = Calendar.from_ical(file_content)
    except Exception as e:
        raise ValueError(f"Invalid ICS file format: {str(e)}")

    event_data = {
        "date": "",
        "participants": "",
        "notes": ""
    }
    
    # We'll just take the first event for now.
    # Context usually implies one meeting transcript context.
    
    for component in cal.walk():
        if component.name == "VEVENT":
            # Extract Date
            dtstart = component.get('dtstart')
            if dtstart:
                dt = dtstart.dt
                if isinstance(dt, datetime):
                    event_data["date"] = dt.strftime("%Y-%m-%d")
                else: # date object (all day event)
                    event_data["date"] = str(dt)
            
            # Extract Participants (ATTENDEE)
            attendees = component.get('attendee')
            if attendees:
                parts = []
                if isinstance(attendees, list):
                    for att in attendees:
                        # Try to get Common Name (CN), fallback to email/string
                        cn = att.params.get('CN')
                        if cn:
                            parts.append(str(cn))
                        else:
                            clean_att = str(att).replace('mailto:', '')
                            parts.append(clean_att)
                    event_data["participants"] = ", ".join(parts)
                else:
                    # Single attendee
                    cn = attendees.params.get('CN')
                    if cn:
                        event_data["participants"] = str(cn)
                    else:
                        event_data["participants"] = str(attendees).replace('mailto:', '')

            # Extract Notes (DESCRIPTION)
            description = component.get('description')
            if description:
                # Clean up description (sometimes has HTML or weird line breaks)
                desc_str = str(description).strip()
                event_data["notes"] = desc_str
                
            # Summary (Title) - Prepend to notes if exists
            summary = component.get('summary')
            if summary:
                 title = str(summary)
                 if event_data["notes"]:
                     event_data["notes"] = f"Meeting Title: {title}\n\n{event_data['notes']}"
                 else:
                     event_data["notes"] = f"Meeting Title: {title}"

            # If we found an event, break (assuming one meeting file)
            break
            
    return event_data
