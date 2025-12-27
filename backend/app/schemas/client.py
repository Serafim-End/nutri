"""
Client Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class IntakeCreateRequest(BaseModel):
    """Request schema for creating an intake form submission."""

    goals: List[str] = Field(default_factory=list, description="Health/nutrition goals")
    dietary_restrictions: List[str] = Field(
        default_factory=list, description="Dietary restrictions"
    )
    budget_min: Optional[int] = Field(None, ge=0, description="Minimum budget in RUB")
    budget_max: Optional[int] = Field(None, ge=0, description="Maximum budget in RUB")
    preferred_schedule: Optional[str] = Field(
        None, description="Preferred schedule: weekdays/weekends/evenings/flexible"
    )
    health_conditions: List[str] = Field(
        default_factory=list, description="Existing health conditions"
    )
    additional_notes: Optional[str] = None


class MatchQuery(BaseModel):
    """Query parameters for nutritionist matching."""

    intake_id: str = Field(..., description="UUID of the intake to match against")


