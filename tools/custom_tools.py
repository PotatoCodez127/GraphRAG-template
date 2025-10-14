# tools/custom_tools.py
import logging
import json
from langchain.tools import StructuredTool
from langchain_core.tools import Tool
from pydantic import ValidationError
from .action_schemas import (
    BookOnboardingCallArgs,
    CheckAvailabilityArgs,
    CancelAppointmentArgs,
    RescheduleAppointmentArgs
)
from .google_calendar import (
    get_available_slots,
    create_calendar_event,
    find_event_by_details,
    update_calendar_event,
    delete_calendar_event
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_availability(date: str) -> str:
    # This function remains the same
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
    # This function remains the same
    logger.info(f"--- ACTION: Booking Zappies AI Onboarding Call ---")
    try:
        data = json.loads(json_string)
        validated_args = BookOnboardingCallArgs(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        return f"I'm sorry, there was a problem with the booking details. Error: {e}"
    full_name, email, company_name, start_time = validated_args.full_name, validated_args.email, validated_args.company_name, validated_args.start_time
    summary = f"Onboard Call with {company_name} | Whatsapp"
    description = f"Onboarding call with {full_name} from {company_name} to discuss the 'Project Pipeline AI'."
    try:
        create_calendar_event(start_time, summary, description, [email])
        return (f"Excellent, {full_name}! I've booked your 'Project Pipeline AI' onboarding call for {start_time}. Our team is excited to connect. ✨")
    except (ValueError, Exception) as e:
        logger.error(f"Booking/validation error: {e}", exc_info=True)
        return f"I'm sorry, I cannot book that appointment. {e}"

# --- NEW JSON-BASED FUNCTIONS ---

def cancel_appointment_from_json(json_string: str) -> str:
    """Cancels an appointment from a JSON string."""
    logger.info(f"--- ACTION: Canceling appointment from JSON ---")
    try:
        data = json.loads(json_string)
        validated_args = CancelAppointmentArgs(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        return f"Sorry, the details provided for cancellation were not valid. Error: {e}"

    email = validated_args.email
    original_start_time = validated_args.original_start_time
    
    event_id = find_event_by_details(email, original_start_time)
    if not event_id:
        return f"I couldn't find an appointment for {email} at that time. Please check the details."
    try:
        delete_calendar_event(event_id)
        return "Your appointment has been successfully canceled."
    except Exception as e:
        logger.error(f"Error canceling event: {e}", exc_info=True)
        return f"Sorry, there was an error canceling your appointment: {str(e)}"

def reschedule_appointment_from_json(json_string: str) -> str:
    """Reschedules an appointment from a JSON string."""
    logger.info(f"--- ACTION: Rescheduling appointment from JSON ---")
    try:
        data = json.loads(json_string)
        validated_args = RescheduleAppointmentArgs(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        return f"Sorry, the details provided for rescheduling were not valid. Error: {e}"

    email = validated_args.email
    original_start_time = validated_args.original_start_time
    new_start_time = validated_args.new_start_time

    event_id = find_event_by_details(email, original_start_time)
    if not event_id:
        return f"I couldn't find an appointment for {email} at the original time. Please check the details."
    try:
        update_calendar_event(event_id, new_start_time)
        return f"Your appointment has been successfully rescheduled to {new_start_time}."
    except Exception as e:
        logger.error(f"Error rescheduling event: {e}", exc_info=True)
        return f"Sorry, there was an error rescheduling your appointment: {str(e)}"

# --- THIS IS THE CRITICAL FIX ---
def get_custom_tools() -> list:
    """Returns a list of all custom tools available to the agent."""
    tools = [
        StructuredTool(
            name="check_availability",
            func=check_availability,
            args_schema=CheckAvailabilityArgs,
            description="Use to check for available 1-hour time slots on a specific date (YYYY-MM-DD)."
        ),
        Tool(
            name="book_zappies_onboarding_call",
            func=book_zappies_onboarding_call_from_json,
            description=(
                "Use to book a NEW onboarding call. The input must be a single, valid JSON string with keys: "
                "'full_name', 'email', 'company_name', and 'start_time'."
            )
        ),
        Tool(
            name="cancel_appointment",
            func=cancel_appointment_from_json,
            description=(
                "Use to cancel an existing appointment. The input must be a single, valid JSON string with keys: "
                "'email' and 'original_start_time'."
            )
        ),
        Tool(
            name="reschedule_appointment",
            func=reschedule_appointment_from_json,
            description=(
                "Use to reschedule an existing appointment. The input must be a single, valid JSON string with keys: "
                "'email', 'original_start_time', and 'new_start_time'."
            )
        )
    ]
    return tools