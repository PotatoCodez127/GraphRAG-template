# tools/action_schemas.py
from pydantic import BaseModel, Field

class BookOnboardingCallArgs(BaseModel):
    """Schema for booking an official onboarding call with the Zappies AI team."""
    full_name: str = Field(description="The full name of the renovation company owner or decision-maker.")
    email: str = Field(description="The business email address where the calendar invite should be sent.")
    company_name: str = Field(description="The name of their renovation company.")