# tools/action_schemas.py
from pydantic import BaseModel, Field

class CheckAvailabilityArgs(BaseModel):
    """Schema for checking available time slots on a given date."""
    date: str = Field(description="The date to check for available slots, in YYYY-MM-DD format.")

class OnboardingCallDetails(BaseModel):
    """The details required to book an onboarding call."""
    full_name: str = Field(description="The full name of the renovation company owner or decision-maker.")
    email: str = Field(description="The business email address where the calendar invite should be sent.")
    company_name: str = Field(description="The name of their renovation company.")
    start_time: str = Field(description="The start time for the meeting in ISO 8601 format (e.g., '2023-10-27T09:00:00').")

class BookOnboardingCallArgs(BaseModel):
    """Schema for booking an official onboarding call with the Zappies AI team."""
    details: OnboardingCallDetails