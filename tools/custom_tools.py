# tools/custom_tools.py
import logging
import json
from langchain.tools import StructuredTool
from langchain_core.tools import Tool
from pydantic import ValidationError
from .action_schemas import BookOnboardingCallArgs, CheckAvailabilityArgs
from .google_calendar import get_available_slots, create_calendar_event

# Set up a basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Tool Functions ---

def check_availability(date: str) -> str:
    # ... (no changes in this function)
    logger.info(f"--- ACTION: Checking availability for {date} ---")
    try:
        data = json.loads(date)
        date_to_check = data.get('date', date)
    except (json.JSONDecodeError, TypeError):
        date_to_check = date
    available_slots = get_available_slots(date_to_check)
    logger.info(f"Available slots: {available_slots}")
    if not available_slots:
        return f"I'm sorry, but there are no available slots on {date_to_check}. Please try another date."
    return f"Here are the available slots for {date_to_check}: {', '.join(available_slots)}"

def book_zappies_onboarding_call_from_json(json_string: str) -> str:
    """Books the onboarding call from a JSON string."""
    logger.info("--- ACTION: Booking Zappies AI Onboarding Call ---")
    logger.info(f"Received raw JSON string: {json_string}")

    try:
        data = json.loads(json_string)
        validated_args = BookOnboardingCallArgs(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        error_message = f"Failed to parse or validate booking details from JSON. Error: {e}"
        logger.error(error_message, exc_info=True)
        return f"I'm sorry, there was a problem with the booking details provided. Please try again. Details: {error_message}"

    full_name = validated_args.full_name
    email = validated_args.email
    company_name = validated_args.company_name
    start_time = validated_args.start_time
        
    logger.info(f"Recipient Name: {full_name}")
    logger.info(f"Recipient Email: {email}")
    logger.info(f"Company: {company_name}")
    logger.info(f"Start Time: {start_time}")

    summary = f"Onboard Call with {company_name} | Whatsapp"
    description = f"Onboarding call with {full_name} from {company_name} to discuss the 'Project Pipeline AI'."
    attendees = [email]

    try:
        create_calendar_event(start_time, summary, description, attendees)
        return (f"Excellent, {full_name}! I've just sent a calendar invitation for your 'Project Pipeline AI' onboarding call to {email} for {start_time}. "
                f"Our team is excited to show you how we can help grow {company_name}. ✨")
    # --- CATCH NEW ERROR ---
    except ValueError as e:
        logger.error(f"Booking validation error: {e}")
        return f"I'm sorry, I cannot book that appointment. {e}"
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}", exc_info=True)
        return f"I'm sorry, but there was an error booking the call: {str(e)}"

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
        Tool(
            name="book_zappies_onboarding_call",
            func=book_zappies_onboarding_call_from_json,
            description=(
                "Use this tool to book a new onboarding call. "
                "The input must be a single, valid JSON string containing the following keys: "
                "'full_name', 'email', 'company_name', and 'start_time'."
            )
        )
    ]
    return tools