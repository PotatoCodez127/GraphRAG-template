# tools/action_schemas.py
from pydantic import BaseModel, Field

# --- Placeholder Tool Schemas ---
# Replace these with schemas specific to your client's needs.

class GatherLeadArgs(BaseModel):
    """Schema for gathering a new business lead."""
    name: str = Field(description="The user's full name.")
    email: str = Field(description="The user's email address.")
    company: str = Field(description="The user's company name.", default="N/A")
    service_interest: str = Field(description="The specific service or product the user is interested in.")

class EscalateToHumanArgs(BaseModel):
    """Schema for escalating the conversation to a human agent."""
    name: str = Field(description="The user's full name.")
    phone: str = Field(description="The user's phone number.")
    reason: str = Field(description="A brief summary of the user's issue or request.")