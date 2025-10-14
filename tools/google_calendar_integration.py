# tools/google_calendar_integration.py
import logging
import os
from datetime import datetime, timedelta, time
import pytz

# Google API Imports
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Local Imports
from config.settings import settings

# --- Setup & Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/calendar"]
SERVICE_ACCOUNT_FILE = "service_account.json"
TIMEZONE = pytz.timezone("Africa/Johannesburg") # SAST for Cape Town

# --- Google Calendar Authentication (Service Account Method) ---
def get_calendar_service():
    """Authenticates with Google using a service account and returns a Calendar service object."""
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(
            f"'{SERVICE_ACCOUNT_FILE}' not found. Please follow the setup instructions."
        )
    
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds)

# --- Slot Finding Helper ---
def find_next_available_slot(service) -> datetime:
    """Finds the next available 60-minute slot from 9 AM to 5 PM on a weekday."""
    now = datetime.now(TIMEZONE)
    start_of_search = now.replace(hour=9, minute=0, second=0, microsecond=0)
    
    if now.hour >= 16:
        start_of_search += timedelta(days=1)
        start_of_search = start_of_search.replace(hour=9, minute=0)

    for i in range(14):
        check_date = (start_of_search + timedelta(days=i)).date()
        
        if check_date.weekday() >= 5:
            continue

        day_start = TIMEZONE.localize(datetime.combine(check_date, time(9, 0)))
        day_end = TIMEZONE.localize(datetime.combine(check_date, time(17, 0)))

        events_result = service.events().list(
            calendarId=settings.GOOGLE_CALENDAR_ID, 
            timeMin=day_start.isoformat(),
            timeMax=day_end.isoformat(), 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        busy_slots = events_result.get('items', [])

        potential_start = day_start
        while potential_start + timedelta(minutes=60) <= day_end:
            is_free = True
            potential_end = potential_start + timedelta(minutes=60)
            
            for event in busy_slots:
                event_start = datetime.fromisoformat(event['start'].get('dateTime'))
                event_end = datetime.fromisoformat(event['end'].get('dateTime'))
                if max(potential_start, event_start) < min(potential_end, event_end):
                    is_free = False
                    break
            
            if is_free:
                return potential_start

            potential_start += timedelta(minutes=15)
            
    return None

# --- Main Calendar Booking Function ---
def book_google_calendar_event(full_name: str, email: str, company_name: str) -> str:
    """Books a Google Calendar appointment."""
    try:
        service = get_calendar_service()
        
        start_time = find_next_available_slot(service)
        if not start_time:
            logger.warning("No available calendar slots found in the next 14 days.")
            return "I'm sorry, I couldn't find an available slot in the calendar. Our team will reach out to you manually to schedule an appointment."
            
        end_time = start_time + timedelta(minutes=60)

        event_body = {
            "summary": f"Zappies AI Onboarding Call: {company_name}",
            "description": f"Onboarding call for {full_name} from {company_name} to discuss the 'Project Pipeline AI'.",
            "start": {"dateTime": start_time.isoformat(), "timeZone": str(TIMEZONE)},
            "end": {"dateTime": end_time.isoformat(), "timeZone": str(TIMEZONE)},
            "attendees": [{"email": email}],
            "reminders": {"useDefault": True},
        }

        created_event = service.events().insert(
            calendarId=settings.GOOGLE_CALENDAR_ID, 
            body=event_body,
            sendNotifications=True
        ).execute()

        logger.info(f"Event successfully created: {created_event.get('htmlLink')}")
        
        friendly_time = start_time.strftime("%A, %B %d at %-I:%M %p")
        
        return (f"Excellent, {full_name}! I've just sent a calendar invitation for your 'Project Pipeline AI' "
                f"onboarding call to {email} for **{friendly_time}**. "
                f"Our team is excited to show you how we can help grow {company_name}. ✨")
                
    except Exception as e:
        logger.error(f"Failed to create calendar event: {e}", exc_info=True)
        return "I'm sorry, I encountered an error while trying to book the calendar appointment. Our team has been notified and will reach out to you shortly."