# tools/custom_tools.py
import logging
from langchain.tools import StructuredTool
from .action_schemas import BookOnboardingCallArgs

# Set up a basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Tool Functions ---

def book_zappies_onboarding_call(name: str, email: str, company_name: str) -> str:
    """Books a 15-minute onboarding call with a potential client. This is the final step."""
    logger.info("--- ACTION: Booking Zappies AI Onboarding Call ---")
    logger.info(f"Recipient Name: {name}")
    logger.info(f"Recipient Email: {email}")
    logger.info(f"Company: {company_name}")
    logger.info("--- END ACTION ---")
    
    return (f"Excellent, {name}! I've just sent a calendar invitation for your 'Project Pipeline AI' onboarding call to {email}. "
            f"Our team is excited to show you how we can help grow {company_name}. ✨")

def request_booking_details() -> str:
    """
    Asks the user for the details needed to book the call, one by one.
    This makes the process more structured and reliable.
    """
    logger.info("--- ACTION: Requesting Booking Details ---")
    return "Great! To get that booked for you, could you please tell me your full name?"

# --- Tool Factory ---
def get_custom_tools() -> list:
    """Returns a list of all custom tools available to the agent."""
    tools = [
        StructuredTool.from_function(
            name="Book Zappies Onboarding Call",
            func=book_zappies_onboarding_call,
            args_schema=BookOnboardingCallArgs,
            description="Use this tool ONLY after you have already collected the user's full name, email, and company name."
        ),
        StructuredTool.from_function(
            name="Request Booking Details",
            func=request_booking_details,
            description="Use this tool when a user agrees to an onboarding call. This tool will ask them for their details."
        )
    ]
    return tools