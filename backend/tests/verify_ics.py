import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.services.ics_parser import parse_ics_data

# Sample ICS content
ics_content = b"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Microsoft Corporation//Outlook 16.0 MIMEDIR//EN
BEGIN:VEVENT
DTSTART:20231024T100000Z
DTEND:20231024T110000Z
SUMMARY:Project Kickoff
DESCRIPTION:Discuss timeline and deliverables.\\n\\nAgenda:\\n1. Intro\\n2. Scope
LOCATION:Conference Room A
ATTENDEE;CN="Alice Smith";RSVP=TRUE:mailto:alice@example.com
ATTENDEE;CN="Bob Jones";RSVP=TRUE:mailto:bob@example.com
END:VEVENT
END:VCALENDAR"""

try:
    print("Testing ICS Parser...")
    data = parse_ics_data(ics_content)
    print("Success!")
    print(f"Date: {data['date']}")
    print(f"Participants: {data['participants']}")
    print(f"Notes: {data['notes']}")
    
    assert data['date'] == "2023-10-24 10:00:00+00:00" or "2023-10-24" in str(data['date'])
    assert "Alice Smith" in data['participants']
    assert "Bob Jones" in data['participants']
    assert "Project Kickoff" in data['notes']
    print("Verification Passed!")
except Exception as e:
    print(f"Verification Failed: {e}")
    exit(1)
