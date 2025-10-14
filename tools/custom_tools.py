# tools/custom_tools.py
import logging
from langchain.tools import Tool # <-- MODIFICATION: Import the base Tool class
from .action_schemas import BookOnboardingCallArgs
# We will import the actual calendar logic from a separate file for cleanliness
from .google_calendar_integration import book_google_calendar_event 

# Set up a basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Tool Functions for Zappies AI's Internal Sales Bot ---

# --- THIS IS THE FINAL ARCHITECTURAL FIX ---
# The function now accepts a single dictionary. The agent's output parser
# will provide this dictionary directly. We then manually validate it with Pydantic.
# This approach is more robust because it bypasses the faulty argument unpacking
# of the StructuredTool.
def book_zappies_onboarding_call(tool_input: dict) -> str:
    """
    Parses a dictionary to book an onboarding call and creates a Google Calendar event.
    The input must be a dictionary with 'full_name', 'email', and 'company_name'.
    """
    try:
        # Manually validate the dictionary using the Pydantic model
        validated_data = BookOnboardingCallArgs.model_validate(tool_input)

        logger.info("--- ACTION: Booking Zappies AI Onboarding Call ---")
        logger.info(f"Validated Data: {validated_data}")

        # Call the actual Google Calendar booking logic from the separate file
        return book_google_calendar_event(
            full_name=validated_data.full_name,
            email=validated_data.email,
            company_name=validated_data.company_name
        )

    except Exception as e:
        # This will catch Pydantic validation errors and other exceptions
        logger.error(f"Failed to validate or book call: {e}", exc_info=True)
        return f"Error: I failed to validate the booking details. Please try again. Details: {e}"
# -------------------------------------------------------------------


# --- Tool Factory ---
def get_custom_tools() -> list:
    """Returns a list of all custom tools available to the agent."""
    tools = [
        # MODIFICATION: Use the standard Tool class
        Tool(
            name="book_zappies_onboarding_call",
            func=book_zappies_onboarding_call,
            description=(
                "Use this tool to book a new onboarding call. The input MUST be a single, valid JSON object "
                "containing the user's 'full_name', 'email', and 'company_name'."
            )
        )
    ]
    return tools