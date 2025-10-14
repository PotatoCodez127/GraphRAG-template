# tools/google_calendar.py
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config.settings import settings
import pytz
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
    sast_tz = pytz.timezone("Africa/Johannesburg")
    # Ensure the start date is timezone-aware from the beginning
    day_start = sast_tz.localize(datetime.datetime.fromisoformat(date))
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
            # Ensure event times from Google are also timezone-aware for comparison
            event_start = parse(event['start'].get('dateTime')).astimezone(sast_tz)
            event_end = parse(event['end'].get('dateTime')).astimezone(sast_tz)
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
    sast_tz = pytz.timezone("Africa/Johannesburg")
    
    # Use dateutil.parser to handle flexible date formats
    naive_start = parse(start_time)
    
    # --- THIS IS THE FIX ---
    # Make the naive datetime object timezone-aware
    start = sast_tz.localize(naive_start)

    # --- ADDED SAFETY CHECKS ---
    now_sast = datetime.datetime.now(sast_tz)
    
    # Check if the requested time is in the past
    if start < now_sast:
        raise ValueError("Cannot book an appointment in the past.")

    # Check if the requested time is for the same day
    if start.date() == now_sast.date():
        raise ValueError("Cannot book a same-day appointment. Please book for the next business day or later.")
    # --- END OF CHECKS ---

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