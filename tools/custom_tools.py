# tools/custom_tools.py
from langchain.tools import StructuredTool
from .action_schemas import GatherLeadArgs, EscalateToHumanArgs

# --- Tool Functions ---
# Replace these functions with your client's actual business logic.
# This is where you would integrate with a CRM, calendar, etc.

def gather_lead(name: str, email: str, company: str, service_interest: str) -> str:
    """Gathers lead information and sends it to the sales team."""
    print("--- ACTION: Capturing New Lead ---")
    print(f"Name: {name}, Email: {email}, Company: {company}, Interest: {service_interest}")
    print("--- END ACTION ---")
    return (f"Thank you, {name}! I've passed your interest in '{service_interest}' "
            f"to our team. They will email you at {email} shortly with more information. ✨")

def escalate_to_human(name: str, phone: str, reason: str) -> str:
    """Handles a user's request to speak to a person."""
    print("--- ACTION: Escalating to Human Support ---")
    print(f"Name: {name}, Phone: {phone}, Reason: {reason}")
    print("--- END ACTION ---")
    return (f"Thank you, {name}. I've created a ticket for our support team. "
            f"Someone will call you at {phone} as soon as possible to help with: '{reason}'.")

# --- Tool Factory ---
# This function dynamically provides the tools to the agent.
# Simply add or remove tools from this list to change the bot's capabilities.
def get_custom_tools() -> list:
    """Returns a list of all custom tools available to the agent."""
    tools = [
        StructuredTool.from_function(
            name="Gather Business Lead",
            func=gather_lead,
            args_schema=GatherLeadArgs,
            description="Use this when a user expresses interest in a product, service, or pricing. You must first ask for their name, email, and what service they are interested in."
        ),
        StructuredTool.from_function(
            name="Escalate to a Human",
            func=escalate_to_human,
            args_schema=EscalateToHumanArgs,
            description="Use this tool when the user explicitly asks to speak to a person, staff member, or human. You must first ask for their name, phone number, and a brief reason for their request."
        )
    ]
    return tools