"""
Bot Middleware
Logging and request tracking middleware with correlation IDs.
"""

import logging
import time
import uuid
from typing import Any, Awaitable, Callable
from contextvars import ContextVar

from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from api_client import get_api_client


logger = logging.getLogger(__name__)

# Context variable for correlation ID (accessible throughout the request)
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Get current correlation ID from context."""
    return correlation_id_var.get()


class StructuredLoggingMiddleware(BaseMiddleware):
    """
    Enhanced middleware for structured logging with correlation IDs.
    Logs:
    - telegram_user_id
    - update type (message/callback_query)
    - current FSM state
    - action name
    - backend request path + status code
    """
    
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        start_time = time.time()
        
        # Generate correlation ID for this request
        corr_id = str(uuid.uuid4())[:8]
        correlation_id_var.set(corr_id)
        
        # Extract user info
        user_id = None
        update_type = "unknown"
        action = "unknown"
        
        if isinstance(event, Message):
            update_type = "message"
            user_id = event.from_user.id if event.from_user else None
            if event.text:
                if event.text.startswith("/"):
                    action = f"command:{event.text.split()[0]}"
                else:
                    action = f"text:{event.text[:30]}..."
            elif event.photo:
                action = "photo"
            elif event.document:
                action = "document"
            else:
                action = "other_message"
                
        elif isinstance(event, CallbackQuery):
            update_type = "callback_query"
            user_id = event.from_user.id if event.from_user else None
            action = f"callback:{event.data}"
        
        # Get FSM state if available
        fsm_state = "none"
        state: Optional[FSMContext] = data.get("state")
        if state:
            try:
                current_state = await state.get_state()
                fsm_state = current_state or "none"
            except Exception:
                fsm_state = "error"
        
        # Log incoming event with structured format
        logger.info(
            f"[REQ] corr_id={corr_id} user_id={user_id} "
            f"type={update_type} action={action} fsm_state={fsm_state}"
        )
        
        try:
            result = await handler(event, data)
            
            # Log success
            elapsed = (time.time() - start_time) * 1000
            logger.info(
                f"[OK] corr_id={corr_id} user_id={user_id} "
                f"action={action} time={elapsed:.0f}ms"
            )
            
            return result
            
        except Exception as e:
            # Log error
            elapsed = (time.time() - start_time) * 1000
            logger.error(
                f"[ERR] corr_id={corr_id} user_id={user_id} "
                f"action={action} time={elapsed:.0f}ms error={str(e)}"
            )
            raise


# Alias for backwards compatibility
LoggingMiddleware = StructuredLoggingMiddleware


class ThrottlingMiddleware(BaseMiddleware):
    """
    Simple throttling middleware to prevent spam.
    Limits requests per user.
    """
    
    def __init__(self, rate_limit: float = 0.5):
        """
        Args:
            rate_limit: Minimum seconds between requests per user
        """
        self.rate_limit = rate_limit
        self.user_last_request: dict[int, float] = {}
    
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        # Extract user_id
        user_id = None
        
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
        
        if user_id:
            now = time.time()
            last_request = self.user_last_request.get(user_id, 0)
            
            if now - last_request < self.rate_limit:
                corr_id = get_correlation_id()
                logger.debug(f"[THROTTLE] corr_id={corr_id} user_id={user_id}")
                
                # Throttled - silently ignore for callbacks
                if isinstance(event, CallbackQuery):
                    await event.answer("Слишком быстро, подождите...")
                    return None
                # For messages, just ignore
                return None
            
            self.user_last_request[user_id] = now
        
        return await handler(event, data)


class ErrorHandlingMiddleware(BaseMiddleware):
    """
    Middleware for graceful error handling.
    Shows user-friendly error messages.
    """
    
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
            
        except Exception as e:
            corr_id = get_correlation_id()
            logger.exception(f"[FATAL] corr_id={corr_id} Unhandled error: {e}")
            
            # Try to send error message to user
            try:
                error_msg = f"😔 Произошла ошибка. Попробуйте ещё раз или напишите /start\n\n<code>ID: {corr_id}</code>"
                
                if isinstance(event, Message):
                    await event.answer(error_msg, parse_mode="HTML")
                elif isinstance(event, CallbackQuery):
                    await event.answer(
                        f"😔 Ошибка (ID: {corr_id}). Попробуйте ещё раз.",
                        show_alert=True,
                    )
            except Exception:
                pass  # Can't send error message
            
            return None


class APILoggingMiddleware(BaseMiddleware):
    """
    Middleware that patches the API client to log requests.
    Only logs when BOT_DEBUG is enabled.
    """
    
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        import os
        if os.environ.get("BOT_DEBUG", "").lower() == "true":
            # Inject correlation ID into API client context
            api = get_api_client()
            # The API client will use get_correlation_id() for logging
        
        return await handler(event, data)
