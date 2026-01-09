"""
Google Calendar Service
Handles OAuth flow and Google Calendar API interactions.
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from flask import current_app, url_for
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.extensions import db
from app.models.google_calendar import GoogleCalendar


class GoogleCalendarService:
    """
    Service for Google Calendar OAuth and API operations.
    """

    # OAuth 2.0 scopes required for Google Calendar
    SCOPES = [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.freebusy",
        "https://www.googleapis.com/auth/calendar.events",  # For creating/deleting events
    ]

    @classmethod
    def get_oauth_flow(cls, nutritionist_id: str = None) -> Flow:
        """
        Create OAuth 2.0 flow for Google Calendar.

        Args:
            nutritionist_id: Optional nutritionist ID for building redirect URI

        Returns:
            Flow instance configured with client credentials
        """
        client_id = current_app.config.get("GOOGLE_CLIENT_ID")
        client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET")
        redirect_uri_template = current_app.config.get("GOOGLE_REDIRECT_URI", "")

        if not all([client_id, client_secret]):
            raise ValueError(
                "Google Calendar OAuth not configured. "
                "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
            )

        # Build redirect URI with nutritionist_id if template provided
        if nutritionist_id and redirect_uri_template and "{nutritionist_id}" in redirect_uri_template:
            redirect_uri = redirect_uri_template.format(nutritionist_id=nutritionist_id)
        elif redirect_uri_template:
            redirect_uri = redirect_uri_template
        elif nutritionist_id:
            # Default redirect URI pattern
            base_url = current_app.config.get('SERVER_NAME', 'http://localhost:5000')
            if not base_url.startswith('http'):
                base_url = f'http://{base_url}'
            redirect_uri = f"{base_url}/api/nutritionists/{nutritionist_id}/calendar/callback"
        else:
            raise ValueError("Redirect URI cannot be determined without nutritionist_id or GOOGLE_REDIRECT_URI")

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri],
                }
            },
            scopes=cls.SCOPES,
        )
        flow.redirect_uri = redirect_uri

        return flow

    @classmethod
    def get_authorization_url(cls, nutritionist_id: str) -> str:
        """
        Generate Google OAuth authorization URL.

        Args:
            nutritionist_id: Nutritionist UUID

        Returns:
            Authorization URL
        """
        flow = cls.get_oauth_flow(nutritionist_id)
        # Store nutritionist_id in state for callback verification
        flow.state = nutritionist_id
        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",  # Force consent to get refresh token
        )
        return authorization_url

    @classmethod
    def handle_oauth_callback(
        cls, authorization_code: str, state: str
    ) -> Optional[GoogleCalendar]:
        """
        Handle OAuth callback and store tokens.

        Args:
            authorization_code: OAuth authorization code from Google
            state: State parameter (should be nutritionist_id)

        Returns:
            GoogleCalendar instance or None if error
        """
        try:
            flow = cls.get_oauth_flow(state)
            flow.fetch_token(code=authorization_code)

            credentials = flow.credentials

            # Get or create GoogleCalendar record
            calendar = GoogleCalendar.query.filter_by(
                nutritionist_id=state
            ).first()

            if not calendar:
                calendar = GoogleCalendar(nutritionist_id=state)
                db.session.add(calendar)

            # Store tokens
            calendar.access_token = credentials.token
            calendar.refresh_token = credentials.refresh_token
            if credentials.expiry:
                calendar.token_expires_at = credentials.expiry
            calendar.is_connected = True
            calendar.connected_at = datetime.now(timezone.utc)
            calendar.disconnected_at = None

            db.session.commit()
            return calendar

        except Exception as e:
            current_app.logger.error(f"Error handling OAuth callback: {e}")
            db.session.rollback()
            return None

    @classmethod
    def get_credentials(cls, calendar: GoogleCalendar) -> Optional[Credentials]:
        """
        Get valid Google credentials for a calendar connection.

        Args:
            calendar: GoogleCalendar instance

        Returns:
            Credentials instance or None if invalid
        """
        if not calendar.is_connected or not calendar.access_token:
            return None

        # Check if token needs refresh
        if calendar.token_expires_at and calendar.token_expires_at <= datetime.now(
            timezone.utc
        ):
            if not calendar.refresh_token:
                return None
            # Refresh token
            credentials = Credentials(
                token=None,
                refresh_token=calendar.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=current_app.config.get("GOOGLE_CLIENT_ID"),
                client_secret=current_app.config.get("GOOGLE_CLIENT_SECRET"),
            )
            credentials.refresh(Flow().request)
            # Update stored token
            calendar.access_token = credentials.token
            if credentials.expiry:
                calendar.token_expires_at = credentials.expiry
            db.session.commit()
        else:
            credentials = Credentials(
                token=calendar.access_token,
                refresh_token=calendar.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=current_app.config.get("GOOGLE_CLIENT_ID"),
                client_secret=current_app.config.get("GOOGLE_CLIENT_SECRET"),
            )

        return credentials

    @classmethod
    def disconnect(cls, nutritionist_id: str) -> bool:
        """
        Disconnect Google Calendar for a nutritionist.

        Args:
            nutritionist_id: Nutritionist UUID

        Returns:
            True if disconnected, False if not found
        """
        calendar = GoogleCalendar.query.filter_by(
            nutritionist_id=nutritionist_id
        ).first()

        if not calendar:
            return False

        calendar.is_connected = False
        calendar.access_token = None
        calendar.refresh_token = None
        calendar.token_expires_at = None
        calendar.selected_calendar_id = None
        calendar.selected_calendar_summary = None
        calendar.disconnected_at = datetime.now(timezone.utc)

        db.session.commit()
        return True

    @classmethod
    def list_calendars(cls, nutritionist_id: str) -> List[Dict[str, Any]]:
        """
        List all calendars for a nutritionist.

        Args:
            nutritionist_id: Nutritionist UUID

        Returns:
            List of calendar dictionaries with id, summary, primary, etc.
        """
        calendar = GoogleCalendar.query.filter_by(
            nutritionist_id=nutritionist_id
        ).first()

        if not calendar or not calendar.is_connected:
            raise ValueError("Google Calendar not connected")

        credentials = cls.get_credentials(calendar)
        if not credentials:
            raise ValueError("Invalid credentials")

        try:
            service = build("calendar", "v3", credentials=credentials)
            calendar_list = service.calendarList().list().execute()

            calendars = []
            for item in calendar_list.get("items", []):
                calendars.append({
                    "id": item.get("id"),
                    "summary": item.get("summary"),
                    "primary": item.get("primary", False),
                    "accessRole": item.get("accessRole"),
                    "backgroundColor": item.get("backgroundColor"),
                    "foregroundColor": item.get("foregroundColor"),
                })

            return calendars

        except HttpError as e:
            current_app.logger.error(f"Error listing calendars: {e}")
            raise ValueError(f"Failed to list calendars: {e}")

    @classmethod
    def select_calendar(
        cls, nutritionist_id: str, calendar_id: str
    ) -> Optional[GoogleCalendar]:
        """
        Select a calendar for a nutritionist.

        Args:
            nutritionist_id: Nutritionist UUID
            calendar_id: Google Calendar ID

        Returns:
            Updated GoogleCalendar instance or None if error
        """
        calendar = GoogleCalendar.query.filter_by(
            nutritionist_id=nutritionist_id
        ).first()

        if not calendar or not calendar.is_connected:
            raise ValueError("Google Calendar not connected")

        credentials = cls.get_credentials(calendar)
        if not credentials:
            raise ValueError("Invalid credentials")

        try:
            service = build("calendar", "v3", credentials=credentials)
            calendar_resource = service.calendars().get(calendarId=calendar_id).execute()

            calendar.selected_calendar_id = calendar_id
            calendar.selected_calendar_summary = calendar_resource.get("summary")
            db.session.commit()

            return calendar

        except HttpError as e:
            current_app.logger.error(f"Error selecting calendar: {e}")
            db.session.rollback()
            raise ValueError(f"Failed to select calendar: {e}")

    @classmethod
    def get_freebusy(
        cls,
        nutritionist_id: str,
        time_min: datetime,
        time_max: datetime,
    ) -> Dict[str, Any]:
        """
        Get free/busy information for the selected calendar.

        Args:
            nutritionist_id: Nutritionist UUID
            time_min: Start time for freebusy query
            time_max: End time for freebusy query

        Returns:
            Dictionary with freebusy data:
            {
                "calendars": {
                    "calendar_id": {
                        "busy": [
                            {"start": "2024-01-01T10:00:00Z", "end": "2024-01-01T11:00:00Z"}
                        ]
                    }
                }
            }

        Note:
            This output can be consumed later to:
            1. Generate availability slots (source="calendar")
            2. Filter out busy times when showing available slots
            3. Sync calendar events with availability slots
        """
        calendar = GoogleCalendar.query.filter_by(
            nutritionist_id=nutritionist_id
        ).first()

        if not calendar or not calendar.is_connected:
            raise ValueError("Google Calendar not connected")

        if not calendar.selected_calendar_id:
            raise ValueError("No calendar selected")

        credentials = cls.get_credentials(calendar)
        if not credentials:
            raise ValueError("Invalid credentials")

        try:
            service = build("calendar", "v3", credentials=credentials)

            # Ensure timezone-aware datetimes
            if time_min.tzinfo is None:
                time_min = time_min.replace(tzinfo=timezone.utc)
            if time_max.tzinfo is None:
                time_max = time_max.replace(tzinfo=timezone.utc)

            body = {
                "timeMin": time_min.isoformat(),
                "timeMax": time_max.isoformat(),
                "items": [{"id": calendar.selected_calendar_id}],
            }

            freebusy_result = service.freebusy().query(body=body).execute()

            return freebusy_result

        except HttpError as e:
            current_app.logger.error(f"Error getting freebusy: {e}")
            raise ValueError(f"Failed to get freebusy: {e}")

    @classmethod
    def create_event(
        cls,
        nutritionist_id: str,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        attendee_email: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a calendar event for a booking.

        Args:
            nutritionist_id: Nutritionist UUID
            summary: Event title/summary
            start_time: Event start time (timezone-aware)
            end_time: Event end time (timezone-aware)
            description: Optional event description
            attendee_email: Optional attendee email (client)

        Returns:
            Google Calendar event ID or None if error
        """
        calendar = GoogleCalendar.query.filter_by(
            nutritionist_id=nutritionist_id
        ).first()

        if not calendar or not calendar.is_connected:
            current_app.logger.debug(
                f"Google Calendar not connected for nutritionist {nutritionist_id}"
            )
            return None

        if not calendar.selected_calendar_id:
            current_app.logger.warning(
                f"No calendar selected for nutritionist {nutritionist_id}"
            )
            return None

        credentials = cls.get_credentials(calendar)
        if not credentials:
            current_app.logger.warning(
                f"Invalid credentials for nutritionist {nutritionist_id}"
            )
            return None

        try:
            service = build("calendar", "v3", credentials=credentials)

            # Ensure timezone-aware datetimes
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)

            event_body = {
                "summary": summary,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": str(start_time.tzinfo),
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": str(end_time.tzinfo),
                },
            }

            if description:
                event_body["description"] = description

            if attendee_email:
                event_body["attendees"] = [{"email": attendee_email}]

            event = (
                service.events()
                .insert(calendarId=calendar.selected_calendar_id, body=event_body)
                .execute()
            )

            event_id = event.get("id")
            current_app.logger.info(
                f"Created calendar event: nutritionist={nutritionist_id}, event_id={event_id}"
            )
            return event_id

        except HttpError as e:
            current_app.logger.error(
                f"Error creating calendar event for nutritionist {nutritionist_id}: {e}"
            )
            return None
        except Exception as e:
            current_app.logger.error(
                f"Unexpected error creating calendar event: {e}"
            )
            return None

    @classmethod
    def delete_event(cls, nutritionist_id: str, event_id: str) -> bool:
        """
        Delete a calendar event.

        Args:
            nutritionist_id: Nutritionist UUID
            event_id: Google Calendar event ID

        Returns:
            True if deleted, False if error or not found
        """
        calendar = GoogleCalendar.query.filter_by(
            nutritionist_id=nutritionist_id
        ).first()

        if not calendar or not calendar.is_connected:
            current_app.logger.debug(
                f"Google Calendar not connected for nutritionist {nutritionist_id}"
            )
            return False

        if not calendar.selected_calendar_id:
            current_app.logger.warning(
                f"No calendar selected for nutritionist {nutritionist_id}"
            )
            return False

        credentials = cls.get_credentials(calendar)
        if not credentials:
            current_app.logger.warning(
                f"Invalid credentials for nutritionist {nutritionist_id}"
            )
            return False

        try:
            service = build("calendar", "v3", credentials=credentials)

            service.events().delete(
                calendarId=calendar.selected_calendar_id, eventId=event_id
            ).execute()

            current_app.logger.info(
                f"Deleted calendar event: nutritionist={nutritionist_id}, event_id={event_id}"
            )
            return True

        except HttpError as e:
            if e.resp.status == 404:
                # Event already deleted or doesn't exist - idempotent success
                current_app.logger.debug(
                    f"Calendar event not found (already deleted?): event_id={event_id}"
                )
                return True
            current_app.logger.error(
                f"Error deleting calendar event for nutritionist {nutritionist_id}: {e}"
            )
            return False
        except Exception as e:
            current_app.logger.error(
                f"Unexpected error deleting calendar event: {e}"
            )
            return False
