"""
Backend API Client
Handles all HTTP communication with the NutriMatch backend.
Uses aiohttp for async requests.
"""

import logging
from typing import Any
from dataclasses import dataclass

import aiohttp

from config import get_config


logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Wrapper for API response."""
    success: bool
    data: dict[str, Any] | None
    error: str | None
    status_code: int


class BackendAPIClient:
    """
    Async HTTP client for backend API.
    All methods are retry-safe and handle errors gracefully.
    """
    
    def __init__(self):
        self.config = get_config()
        self.base_url = self.config.backend_url
        self.session: aiohttp.ClientSession | None = None
    
    def _get_headers(self) -> dict[str, str]:
        """Get default headers with service token."""
        return {
            "Content-Type": "application/json",
            "X-Service-Token": self.config.service_token,
        }
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure aiohttp session exists."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> APIResponse:
        """Make HTTP request to backend."""
        url = f"{self.base_url}{endpoint}"
        session = await self._ensure_session()
        
        try:
            async with session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=self._get_headers(),
            ) as response:
                response_data = None
                try:
                    response_data = await response.json()
                except Exception:
                    pass
                
                if response.status >= 400:
                    error_msg = "Request failed"
                    if response_data and "error" in response_data:
                        error_msg = response_data["error"]
                    logger.warning(
                        f"API request failed: {method} {endpoint} -> {response.status}: {error_msg}"
                    )
                    return APIResponse(
                        success=False,
                        data=response_data,
                        error=error_msg,
                        status_code=response.status,
                    )
                
                logger.debug(f"API request success: {method} {endpoint} -> {response.status}")
                return APIResponse(
                    success=True,
                    data=response_data,
                    error=None,
                    status_code=response.status,
                )
                
        except aiohttp.ClientError as e:
            logger.error(f"API connection error: {method} {endpoint} -> {e}")
            return APIResponse(
                success=False,
                data=None,
                error=f"Connection error: {str(e)}",
                status_code=0,
            )
        except Exception as e:
            logger.error(f"API unexpected error: {method} {endpoint} -> {e}")
            return APIResponse(
                success=False,
                data=None,
                error=f"Unexpected error: {str(e)}",
                status_code=0,
            )
    
    # ==========================================
    # Auth & User Resolution
    # ==========================================
    
    async def resolve_telegram_user(self, telegram_user_id: int) -> APIResponse:
        """
        Resolve Telegram user to get profile and role.
        GET /api/bot/resolve-telegram-user?telegram_user_id=123
        """
        return await self._request(
            "GET",
            "/api/bot/resolve-telegram-user",
            params={"telegram_user_id": telegram_user_id},
        )
    
    # ==========================================
    # Nutritionist Profile
    # ==========================================
    
    async def upsert_nutritionist(
        self,
        telegram_user_id: int,
        full_name: str,
        photo_url: str | None = None,
        bio: str | None = None,
        tags: list[str] | None = None,
        specializations: list[str] | None = None,
        submit_for_verification: bool = False,
    ) -> APIResponse:
        """
        Create or update nutritionist profile.
        POST /api/nutritionists/upsert
        """
        data = {
            "telegram_user_id": telegram_user_id,
            "full_name": full_name,
            "submit_for_verification": submit_for_verification,
        }
        if photo_url:
            data["photo_url"] = photo_url
        if bio:
            data["bio"] = bio
        if tags:
            data["tags"] = tags
        if specializations:
            data["specializations"] = specializations
        
        return await self._request("POST", "/api/nutritionists/upsert", data=data)
    
    async def get_nutritionist_dashboard(self, nutritionist_id: str) -> APIResponse:
        """
        Get nutritionist dashboard data.
        GET /api/nutritionists/<id>/dashboard
        """
        return await self._request("GET", f"/api/nutritionists/{nutritionist_id}/dashboard")
    
    async def upload_photo(
        self,
        nutritionist_id: str,
        photo_bytes: bytes,
        filename: str,
    ) -> APIResponse:
        """
        Upload photo to backend.
        POST /api/bot/nutritionists/<id>/upload-photo (multipart)
        """
        url = f"{self.base_url}/api/bot/nutritionists/{nutritionist_id}/upload-photo"
        session = await self._ensure_session()
        
        try:
            form_data = aiohttp.FormData()
            form_data.add_field(
                "photo",
                photo_bytes,
                filename=filename,
                content_type="image/jpeg",
            )
            
            headers = {"X-Service-Token": self.config.service_token}
            
            async with session.post(url, data=form_data, headers=headers) as response:
                response_data = None
                try:
                    response_data = await response.json()
                except Exception:
                    pass
                
                if response.status >= 400:
                    error_msg = response_data.get("error", "Upload failed") if response_data else "Upload failed"
                    return APIResponse(
                        success=False,
                        data=response_data,
                        error=error_msg,
                        status_code=response.status,
                    )
                
                return APIResponse(
                    success=True,
                    data=response_data,
                    error=None,
                    status_code=response.status,
                )
                
        except Exception as e:
            logger.error(f"Photo upload error: {e}")
            return APIResponse(
                success=False,
                data=None,
                error=f"Upload error: {str(e)}",
                status_code=0,
            )
    
    # ==========================================
    # Services
    # ==========================================
    
    async def list_services(self, nutritionist_id: str) -> APIResponse:
        """
        List nutritionist's services.
        GET /api/bot/nutritionists/<id>/services
        """
        return await self._request("GET", f"/api/bot/nutritionists/{nutritionist_id}/services")
    
    async def create_service(
        self,
        nutritionist_id: str,
        title: str,
        duration_minutes: int,
        price_rub: int,
        description: str | None = None,
        is_active: bool = True,
    ) -> APIResponse:
        """
        Create a new service.
        POST /api/nutritionists/<id>/services
        """
        data = {
            "title": title,
            "duration_minutes": duration_minutes,
            "price_rub": price_rub,
            "is_active": is_active,
        }
        if description:
            data["description"] = description
        
        return await self._request(
            "POST",
            f"/api/nutritionists/{nutritionist_id}/services",
            data=data,
        )
    
    async def update_service(
        self,
        nutritionist_id: str,
        service_id: str,
        title: str | None = None,
        duration_minutes: int | None = None,
        price_rub: int | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> APIResponse:
        """
        Update a service.
        PUT /api/bot/nutritionists/<id>/services/<service_id>
        """
        data = {}
        if title is not None:
            data["title"] = title
        if duration_minutes is not None:
            data["duration_minutes"] = duration_minutes
        if price_rub is not None:
            data["price_rub"] = price_rub
        if description is not None:
            data["description"] = description
        if is_active is not None:
            data["is_active"] = is_active
        
        return await self._request(
            "PUT",
            f"/api/bot/nutritionists/{nutritionist_id}/services/{service_id}",
            data=data,
        )
    
    async def delete_service(self, nutritionist_id: str, service_id: str) -> APIResponse:
        """
        Delete a service.
        DELETE /api/bot/nutritionists/<id>/services/<service_id>
        """
        return await self._request(
            "DELETE",
            f"/api/bot/nutritionists/{nutritionist_id}/services/{service_id}",
        )
    
    # ==========================================
    # Calendar
    # ==========================================
    
    async def get_calendar_status(self, nutritionist_id: str) -> APIResponse:
        """
        Get calendar connection status.
        GET /api/bot/nutritionists/<id>/calendar/status
        """
        return await self._request("GET", f"/api/bot/nutritionists/{nutritionist_id}/calendar/status")
    
    async def get_google_oauth_url(self, nutritionist_id: str) -> APIResponse:
        """
        Get Google OAuth URL for calendar connection.
        GET /api/bot/nutritionists/<id>/calendar/oauth-url
        """
        return await self._request("GET", f"/api/bot/nutritionists/{nutritionist_id}/calendar/oauth-url")
    
    # ==========================================
    # Reviews
    # ==========================================
    
    async def get_reviews(
        self,
        nutritionist_id: str,
        limit: int = 5,
        offset: int = 0,
    ) -> APIResponse:
        """
        Get nutritionist reviews.
        GET /api/bot/nutritionists/<id>/reviews
        """
        return await self._request(
            "GET",
            f"/api/bot/nutritionists/{nutritionist_id}/reviews",
            params={"limit": limit, "offset": offset},
        )
    
    # ==========================================
    # Statistics
    # ==========================================
    
    async def get_statistics(self, nutritionist_id: str, days: int = 30) -> APIResponse:
        """
        Get nutritionist statistics.
        GET /api/bot/nutritionists/<id>/statistics
        """
        return await self._request(
            "GET",
            f"/api/bot/nutritionists/{nutritionist_id}/statistics",
            params={"days": days},
        )
    
    # ==========================================
    # Support
    # ==========================================
    
    async def send_support_message(
        self,
        telegram_user_id: int,
        message: str,
    ) -> APIResponse:
        """
        Send support message.
        POST /api/bot/support/messages
        """
        return await self._request(
            "POST",
            "/api/bot/support/messages",
            data={
                "telegram_user_id": telegram_user_id,
                "message": message,
            },
        )
    
    # ==========================================
    # Filter Options (for specializations)
    # ==========================================
    
    async def get_filter_options(self) -> APIResponse:
        """
        Get available filter options (goals, specializations, etc.).
        GET /api/public/filters/options
        """
        return await self._request("GET", "/api/public/filters/options")


# Global client instance
_client: BackendAPIClient | None = None


def get_api_client() -> BackendAPIClient:
    """Get or create API client instance."""
    global _client
    if _client is None:
        _client = BackendAPIClient()
    return _client


async def close_api_client():
    """Close the global API client."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None

