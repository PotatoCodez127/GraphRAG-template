# tools/custom_tools.py
import logging
from langchain.tools import StructuredTool
from .action_schemas import BookOnboardingCallArgs

# Set up a basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Tool Functions for Zappies AI's Internal Sales Bot ---

def book_zappies_onboarding_call(data: BookOnboardingCallArgs) -> str:
    """Books a 15-minute onboarding call with a potential client to discuss the 'Project Pipeline AI'."""
    name = data.full_name
    email = data.email
    company_name = data.company_name

    logger.info("--- ACTION: Booking Zappies AI Onboarding Call ---")
    logger.info(f"Recipient Name: {name}")
    logger.info(f"Recipient Email: {email}")
    logger.info(f"Company: {company_name}")
    logger.info("--- END ACTION ---")
    
    return (f"Excellent, {name}! I've just sent a calendar invitation for your 'Project Pipeline AI' onboarding call to {email}. "
            f"Our team is excited to show you how we can help grow {company_name}. ✨")

# --- Tool Factory ---
def get_custom_tools() -> list:
    """Returns a list of all custom tools available to the agent."""
    tools = [
        StructuredTool.from_function(
            name="book_zappies_onboarding_call",
            func=book_zappies_onboarding_call,
            args_schema=BookOnboardingCallArgs,
            description="Use this tool to book a new onboarding call ONLY after you have collected the user's full name, email, and company name AND after the user has confirmed these details are correct."
        )
    ]
    return tools