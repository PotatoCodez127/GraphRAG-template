# tools/custom_tools.py
import logging
import json
from langchain.tools import StructuredTool
from .action_schemas import BookOnboardingCallArgs, CheckAvailabilityArgs
from .google_calendar import get_available_slots, create_calendar_event

# Set up a basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Tool Functions ---

def check_availability(date: str) -> str:
    """Checks for available 15-minute slots on a given date."""
    logger.info(f"--- ACTION: Checking availability for {date} ---")
    
    try:
        # Langchain can sometimes pass the arguments as a JSON string
        # when there's only one argument.
        data = json.loads(date)
        date_to_check = data.get('date', date)
    except (json.JSONDecodeError, TypeError):
        # If it's not a JSON string, assume it's the date itself.
        date_to_check = date

    available_slots = get_available_slots(date_to_check)
    logger.info(f"Available slots: {available_slots}")
    logger.info("--- END ACTION ---")
    if not available_slots:
        return f"I'm sorry, but there are no available slots on {date_to_check}. Please try another date."
    return f"Here are the available slots for {date_to_check}: {', '.join(available_slots)}"

def book_zappies_onboarding_call(full_name: str, email: str, company_name: str, start_time: str) -> str:
    """Books a 15-minute onboarding call with a potential client to discuss the 'Project Pipeline AI'."""
    logger.info("--- ACTION: Booking Zappies AI Onboarding Call ---")
    
    try:
        # The arguments can sometimes be passed as a single JSON string.
        # We need to handle this case.
        if isinstance(full_name, str) and full_name.startswith('{'):
            data = json.loads(full_name)
            full_name = data.get('full_name')
            email = data.get('email')
            company_name = data.get('company_name')
            start_time = data.get('start_time')

    except (json.JSONDecodeError, TypeError):
        pass # If it's not a JSON string, we can assume the arguments are correct.
        
    logger.info(f"Recipient Name: {full_name}")
    logger.info(f"Recipient Email: {email}")
    logger.info(f"Company: {company_name}")
    logger.info(f"Start Time: {start_time}")

    summary = f"Project Pipeline AI Onboarding Call with {company_name}"
    description = f"Onboarding call with {full_name} from {company_name} to discuss the 'Project Pipeline AI'."
    attendees = [email]

    try:
        create_calendar_event(start_time, summary, description, attendees)
        logger.info("--- END ACTION ---")
        return (f"Excellent, {full_name}! I've just sent a calendar invitation for your 'Project Pipeline AI' onboarding call to {email} for {start_time}. "
                f"Our team is excited to show you how we can help grow {company_name}. ✨")
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}")
        return "I'm sorry, but there was an error booking the call. Please try again later."


# --- Tool Factory ---
def get_custom_tools() -> list:
    """Returns a list of all custom tools available to the agent."""
    tools = [
        StructuredTool.from_function(
            name="check_availability",
            func=check_availability,
            args_schema=CheckAvailabilityArgs,
            description="Use this tool to check for available time slots on a specific date."
        ),
        StructuredTool.from_function(
            name="book_zappies_onboarding_call",
            func=book_zappies_onboarding_call,
            args_schema=BookOnboardingCallArgs,
            description="Use this tool to book a new onboarding call ONLY after you have collected the user's full name, email, company name, and desired start time AND after the user has confirmed these details are correct."
        )
    ]
    return tools