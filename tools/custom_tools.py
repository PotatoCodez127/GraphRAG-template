# tools/custom_tools.py
from config.settings import settings
from supabase.client import Client, create_client
import logging
import json
from langchain.tools import StructuredTool
from langchain_core.tools import Tool
from pydantic import ValidationError
from .action_schemas import (
    BookOnboardingCallArgs,
    CheckAvailabilityArgs,
    CancelAppointmentArgs,
    RescheduleAppointmentArgs,
    RequestHumanHandoverArgs
)
from .google_calendar import (
    get_available_slots,
    create_calendar_event,
    find_event_by_details,
    update_calendar_event,
    delete_calendar_event
)
from .email_sender import send_confirmation_email

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
    logger.info(f"--- ACTION: Booking Zappies AI Onboarding Call ---")
    try:
        data = json.loads(json_string)
        validated_args = BookOnboardingCallArgs(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        return f"I'm sorry, there was a problem with the booking details. Error: {e}"

    if validated_args.monthly_budget < 8000:
        return (
            "Thank you for sharing that. Based on the budget you provided, it seems like our 'Project Pipeline AI' "
            "might not be the right fit for your needs at this moment. Our solution is designed for businesses with a "
            "higher budget for this kind of automation. I appreciate your time and honesty!"
        )

    # Deconstruct the validated arguments
    full_name = validated_args.full_name
    email = validated_args.email
    company_name = validated_args.company_name
    start_time = validated_args.start_time
    goal = validated_args.goal
    monthly_budget = validated_args.monthly_budget

    summary = f"Onboard Call with {company_name} | Zappies AI"
    description = (
        f"Onboarding call with {full_name} from {company_name} to discuss the 'Project Pipeline AI'.\n\n"
        f"Stated Goal: {goal}\n"
        f"Stated Budget: R{monthly_budget}/month"
    )
    
    try:
        
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        
        # Insert the meeting details into Supabase without a calendar event ID
        response = supabase.table("meetings").insert({
            # "google_calendar_event_id" is now omitted
            "full_name": full_name,
            "email": email,
            "company_name": company_name,
            "start_time": start_time,
            "goal": goal,
            "monthly_budget": monthly_budget,
            "status": "pending_confirmation"
        }).execute()
        
        meeting_id = response.data[0]['id']

        send_confirmation_email(
            recipient_email=email,
            full_name=full_name,
            start_time=start_time,
            meeting_id=meeting_id
        )

        return (f"Excellent, {full_name}! I've provisionally booked your onboarding call. "
                "I've just sent you an email to confirm your spot. Please click the link in the email to finalize everything. ✨")
    except (ValueError, Exception) as e:
        logger.error(f"Booking/validation error: {e}", exc_info=True)
        return f"I'm sorry, I cannot book that appointment. {e}"

def request_human_handover(json_string: str) -> str:
    """Handles the human handover process."""
    logger.info(f"--- ACTION: Requesting Human Handover ---")
    try:
        data = json.loads(json_string)
        # We only need the conversation_id, which the agent already knows
        conversation_id = data["conversation_id"]
    except (json.JSONDecodeError, KeyError) as e:
        return f"Sorry, there was an internal error processing the handover request. Error: {e}"

    try:
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

        # 1. Fetch the conversation history
        response = supabase.table("conversation_history").select("history").eq("conversation_id", conversation_id).single().execute()
        
        if not response.data or not response.data.get('history'):
            return "Could not find the conversation history to perform the handover."

        from langchain_core.messages import messages_from_dict
        history_messages = messages_from_dict(response.data['history'])

        # 2. Send the notification email
        send_handover_email(conversation_id, history_messages)

        # 3. Update the conversation status in the database
        supabase.table("conversation_history").update({"status": "handover"}).eq("conversation_id", conversation_id).execute()
        
        return "Okay, I've notified a member of our team. They will review our conversation and get back to you here as soon as possible."

    except Exception as e:
        logger.error(f"Error during handover for convo {conversation_id}: {e}", exc_info=True)
        return "Sorry, I encountered an error while trying to reach a human. Please try again."

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
                "Use to book a NEW onboarding call after you have collected all required information. The input must be a single, "
                "valid JSON string with keys: 'full_name', 'email', 'company_name', 'start_time', 'goal', and 'monthly_budget'."
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
        ),
        Tool(
            name="request_human_handover",
            func=request_human_handover,
            description=(
                "Use this tool when the user explicitly asks to speak to a human, a person, or a team member. "
                "The input MUST be a single, valid JSON string with the key: 'conversation_id'."
            )
        )
    ]
    return tools

