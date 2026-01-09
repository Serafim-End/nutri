"""
Google Calendar Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CalendarInfo(BaseModel):
    """Calendar information from Google Calendar API."""

    id: str = Field(..., description="Calendar ID")
    summary: str = Field(..., description="Calendar name")
    primary: bool = Field(default=False, description="Whether this is the primary calendar")
    accessRole: str = Field(..., description="Access role (owner, reader, etc.)")
    backgroundColor: Optional[str] = Field(None, description="Background color")
    foregroundColor: Optional[str] = Field(None, description="Foreground color")


class GoogleCalendarConnectionResponse(BaseModel):
    """Response schema for Google Calendar connection status."""

    id: str
    nutritionist_id: str
    is_connected: bool
    selected_calendar_id: Optional[str] = None
    selected_calendar_summary: Optional[str] = None
    connected_at: Optional[str] = None
    disconnected_at: Optional[str] = None


class CalendarListResponse(BaseModel):
    """Response schema for listing calendars."""

    calendars: List[CalendarInfo]


class SelectCalendarRequest(BaseModel):
    """Request schema for selecting a calendar."""

    calendar_id: str = Field(..., description="Google Calendar ID to select")


class FreeBusyRequest(BaseModel):
    """Request schema for freebusy query."""

    time_min: datetime = Field(..., description="Start time for freebusy query")
    time_max: datetime = Field(..., description="End time for freebusy query")


class FreeBusyResponse(BaseModel):
    """Response schema for freebusy query."""

    calendars: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Freebusy data per calendar. Each calendar has a 'busy' array with time ranges."
    )
    timeMin: str = Field(..., description="Start time of the query")
    timeMax: str = Field(..., description="End time of the query")
