# tools/custom_tools.py
import logging
import json
from langchain.tools import Tool # <-- MODIFICATION: Import the base Tool class
from .action_schemas import BookOnboardingCallArgs

# Set up a basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Tool Functions for Zappies AI's Internal Sales Bot ---

# --- THIS IS THE FINAL ARCHITECTURAL FIX ---
# The function now accepts a single string argument. We know from the error logs
# that the AgentExecutor is providing the JSON object as a string.
# We will manually parse and validate this string using our Pydantic model.
# This approach is more robust as it bypasses the faulty argument unpacking
# of the StructuredTool.
def book_zappies_onboarding_call(tool_input: str) -> str:
    """
    Parses a JSON string to book a 15-minute onboarding call with a potential client.
    The input must be a JSON string with 'full_name', 'email', and 'company_name'.
    """
    try:
        # Manually parse the JSON string into our Pydantic model
        data = BookOnboardingCallArgs.model_validate_json(tool_input)

        logger.info("--- ACTION: Booking Zappies AI Onboarding Call ---")
        logger.info(f"Recipient Name: {data.full_name}")
        logger.info(f"Recipient Email: {data.email}")
        logger.info(f"Company: {data.company_name}")
        logger.info("--- END ACTION ---")
        
        return (f"Excellent, {data.full_name}! I've just sent a calendar invitation for your 'Project Pipeline AI' onboarding call to {data.email}. "
                f"Our team is excited to show you how we can help grow {data.company_name}. ✨")

    except json.JSONDecodeError:
        return "Error: The provided input was not valid JSON."
    except Exception as e:
        # This will catch Pydantic validation errors and other exceptions
        return f"Error: Failed to validate booking details. Details: {e}"
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
                "Use this tool to book a new onboarding call. The input MUST be a single, valid JSON object string "
                "containing the user's 'full_name', 'email', and 'company_name'."
            )
        )
    ]
    return tools