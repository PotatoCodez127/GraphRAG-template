# tools/google_calendar.py
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config.settings import settings
import pytz
# --- CORRECTED IMPORT ---
from dateutil.parser import parse

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = settings.SERVICE_ACCOUNT_FILE
CALENDAR_ID = settings.GOOGLE_CALENDAR_ID

def get_calendar_service():
    """Returns an authenticated Google Calendar service object."""
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service

def get_available_slots(date: str) -> list[str]:
    """
    Checks for available 15-minute slots on a given date.
    Returns a list of available start times in ISO 8601 format.
    """
    service = get_calendar_service()
    day_start = datetime.datetime.fromisoformat(date).astimezone(pytz.timezone("Africa/Johannesburg"))
    day_end = day_start + datetime.timedelta(days=1)

    # Get all events for the given day
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=day_start.isoformat(),
        timeMax=day_end.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    # Define working hours (e.g., 9 AM to 5 PM)
    working_hours_start = day_start.replace(hour=9, minute=0, second=0, microsecond=0)
    working_hours_end = day_start.replace(hour=17, minute=0, second=0, microsecond=0)

    available_slots = []
    current_time = working_hours_start

    while current_time < working_hours_end:
        slot_end = current_time + datetime.timedelta(minutes=15)
        is_free = True

        for event in events:
            event_start = datetime.datetime.fromisoformat(event['start'].get('dateTime'))
            event_end = datetime.datetime.fromisoformat(event['end'].get('dateTime'))
            if not (slot_end <= event_start or current_time >= event_end):
                is_free = False
                break

        if is_free:
            available_slots.append(current_time.isoformat())
        
        current_time = slot_end

    return available_slots

def create_calendar_event(start_time: str, summary: str, description: str, attendees: list[str]) -> dict:
    """
    Creates a new event in the Google Calendar.
    """
    service = get_calendar_service()
    
    # Use dateutil.parser to handle more flexible date formats
    start = parse(start_time)
    end = start + datetime.timedelta(minutes=15)

    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start.isoformat(),
            'timeZone': 'Africa/Johannesburg',
        },
        'end': {
            'dateTime': end.isoformat(),
            'timeZone': 'Africa/Johannesburg',
        },
        'attendees': [{'email': email} for email in attendees],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }

    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return created_event