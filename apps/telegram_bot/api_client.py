"""
Backend API Client
Handles all HTTP communication with the NutriMatch backend.
Uses aiohttp for async requests with correlation ID logging.
"""

import logging
from typing import Any, Optional
from dataclasses import dataclass

import aiohttp

from config import get_config


logger = logging.getLogger(__name__)


def _get_correlation_id() -> str:
    """Get correlation ID from middleware context."""
    try:
        from middleware import get_correlation_id
        return get_correlation_id()
    except Exception:
        return ""


@dataclass
class APIResponse:
    """Wrapper for API response."""
    success: bool
    data: Optional[dict[str, Any]]
    error: Optional[str]
    status_code: int


class BackendAPIClient:
    """
    Async HTTP client for backend API.
    All methods are retry-safe and handle errors gracefully.
    Includes correlation ID logging for request tracing.
    """
    
    def __init__(self):
        self.config = get_config()
        self.base_url = self.config.backend_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    def _get_headers(self) -> dict[str, str]:
        """Get default headers with service token."""
        headers = {
            "Content-Type": "application/json",
            "X-Service-Token": self.config.service_token,
        }
        
        # Add correlation ID if available
        corr_id = _get_correlation_id()
        if corr_id:
            headers["X-Correlation-ID"] = corr_id
        
        return headers
    
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
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> APIResponse:
        """Make HTTP request to backend with structured logging."""
        url = f"{self.base_url}{endpoint}"
        session = await self._ensure_session()
        corr_id = _get_correlation_id()
        
        try:
            logger.debug(
                f"[API] corr_id={corr_id} method={method} endpoint={endpoint}"
            )
            
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
                        f"[API] corr_id={corr_id} {method} {endpoint} "
                        f"status={response.status} error={error_msg}"
                    )
                    return APIResponse(
                        success=False,
                        data=response_data,
                        error=error_msg,
                        status_code=response.status,
                    )
                
                logger.debug(
                    f"[API] corr_id={corr_id} {method} {endpoint} "
                    f"status={response.status} OK"
                )
                return APIResponse(
                    success=True,
                    data=response_data,
                    error=None,
                    status_code=response.status,
                )
                
        except aiohttp.ClientError as e:
            logger.error(
                f"[API] corr_id={corr_id} {method} {endpoint} "
                f"connection_error={e}"
            )
            return APIResponse(
                success=False,
                data=None,
                error=f"Connection error: {str(e)}",
                status_code=0,
            )
        except Exception as e:
            logger.error(
                f"[API] corr_id={corr_id} {method} {endpoint} "
                f"unexpected_error={e}"
            )
            return APIResponse(
                success=False,
                data=None,
                error=f"Unexpected error: {str(e)}",
                status_code=0,
            )
    
    # ==========================================
    # Health Check (for smoke tests)
    # ==========================================
    
    async def health_check(self) -> APIResponse:
        """
        Check backend health.
        GET /health/db
        """
        url = f"{self.base_url}/health/db"
        session = await self._ensure_session()
        
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                try:
                    data = await response.json()
                except Exception:
                    data = None
                
                return APIResponse(
                    success=response.status == 200,
                    data=data,
                    error=None if response.status == 200 else "Health check failed",
                    status_code=response.status,
                )
        except Exception as e:
            return APIResponse(
                success=False,
                data=None,
                error=str(e),
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
        photo_url: Optional[str] = None,
        bio: Optional[str] = None,
        tags: Optional[list[str]] = None,
        specializations: Optional[list[str]] = None,
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
        corr_id = _get_correlation_id()
        
        try:
            form_data = aiohttp.FormData()
            form_data.add_field(
                "photo",
                photo_bytes,
                filename=filename,
                content_type="image/jpeg",
            )
            
            headers = {"X-Service-Token": self.config.service_token}
            if corr_id:
                headers["X-Correlation-ID"] = corr_id
            
            async with session.post(url, data=form_data, headers=headers) as response:
                response_data = None
                try:
                    response_data = await response.json()
                except Exception:
                    pass
                
                if response.status >= 400:
                    error_msg = response_data.get("error", "Upload failed") if response_data else "Upload failed"
                    logger.warning(
                        f"[API] corr_id={corr_id} POST upload-photo "
                        f"status={response.status} error={error_msg}"
                    )
                    return APIResponse(
                        success=False,
                        data=response_data,
                        error=error_msg,
                        status_code=response.status,
                    )
                
                logger.debug(
                    f"[API] corr_id={corr_id} POST upload-photo "
                    f"status={response.status} OK"
                )
                return APIResponse(
                    success=True,
                    data=response_data,
                    error=None,
                    status_code=response.status,
                )
                
        except Exception as e:
            logger.error(f"[API] corr_id={corr_id} Photo upload error: {e}")
            return APIResponse(
                success=False,
                data=None,
                error=f"Upload error: {str(e)}",
                status_code=0,
            )
    
    async def upload_document(
        self,
        nutritionist_id: str,
        file_bytes: bytes,
        filename: str,
        document_type: str,
    ) -> APIResponse:
        """
        Upload document to backend.
        POST /api/bot/nutritionists/<id>/documents/upload (multipart)
        """
        url = f"{self.base_url}/api/bot/nutritionists/{nutritionist_id}/documents/upload"
        session = await self._ensure_session()
        corr_id = _get_correlation_id()
        
        try:
            # Determine content type
            content_type = "application/octet-stream"
            if filename.lower().endswith(".pdf"):
                content_type = "application/pdf"
            elif filename.lower().endswith((".jpg", ".jpeg")):
                content_type = "image/jpeg"
            elif filename.lower().endswith(".png"):
                content_type = "image/png"
            
            form_data = aiohttp.FormData()
            form_data.add_field(
                "file",
                file_bytes,
                filename=filename,
                content_type=content_type,
            )
            form_data.add_field("type", document_type)
            
            headers = {"X-Service-Token": self.config.service_token}
            if corr_id:
                headers["X-Correlation-ID"] = corr_id
            
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
            logger.error(f"[API] corr_id={corr_id} Document upload error: {e}")
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
        description: Optional[str] = None,
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
        title: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        price_rub: Optional[int] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
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
    
    # ==========================================
    # Availability Slots
    # ==========================================
    
    async def get_slots(
        self,
        nutritionist_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> APIResponse:
        """
        Get nutritionist's availability slots.
        GET /api/bot/nutritionists/<id>/slots
        """
        params = {}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        
        return await self._request(
            "GET",
            f"/api/bot/nutritionists/{nutritionist_id}/slots",
            params=params if params else None,
        )
    
    async def create_slot(
        self,
        nutritionist_id: str,
        start_at: str,
        end_at: str,
    ) -> APIResponse:
        """
        Create a new availability slot.
        POST /api/bot/nutritionists/<id>/slots
        """
        return await self._request(
            "POST",
            f"/api/bot/nutritionists/{nutritionist_id}/slots",
            data={
                "start_at": start_at,
                "end_at": end_at,
            },
        )
    
    async def delete_slot(
        self,
        nutritionist_id: str,
        slot_id: str,
    ) -> APIResponse:
        """
        Delete an availability slot.
        DELETE /api/bot/nutritionists/<id>/slots/<slot_id>
        """
        return await self._request(
            "DELETE",
            f"/api/bot/nutritionists/{nutritionist_id}/slots/{slot_id}",
        )
    
    # ==========================================
    # Nutritionist Bookings
    # ==========================================
    
    async def get_nutritionist_bookings(
        self,
        nutritionist_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> APIResponse:
        """
        Get nutritionist's bookings.
        GET /api/bot/nutritionists/<id>/bookings
        """
        return await self._request(
            "GET",
            f"/api/bot/nutritionists/{nutritionist_id}/bookings",
            params={"limit": limit, "offset": offset},
        )


# Global client instance
_client: Optional[BackendAPIClient] = None


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
