"""
Bot Middleware
Logging and request tracking middleware.
"""

import logging
import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery


logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware for structured logging of all bot interactions.
    Logs user_id, action type, and timing information.
    """
    
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        start_time = time.time()
        
        # Extract user info
        user_id = None
        action = "unknown"
        
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            if event.text:
                if event.text.startswith("/"):
                    action = f"command:{event.text.split()[0]}"
                else:
                    action = "message"
            elif event.photo:
                action = "photo"
            elif event.document:
                action = "document"
            else:
                action = "other_message"
                
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
            action = f"callback:{event.data}"
        
        # Log incoming event
        logger.info(
            f"[IN] user_id={user_id} action={action}"
        )
        
        try:
            result = await handler(event, data)
            
            # Log success
            elapsed = (time.time() - start_time) * 1000
            logger.info(
                f"[OK] user_id={user_id} action={action} time={elapsed:.0f}ms"
            )
            
            return result
            
        except Exception as e:
            # Log error
            elapsed = (time.time() - start_time) * 1000
            logger.error(
                f"[ERR] user_id={user_id} action={action} time={elapsed:.0f}ms error={str(e)}"
            )
            raise


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
            logger.exception(f"Unhandled error: {e}")
            
            # Try to send error message to user
            try:
                if isinstance(event, Message):
                    await event.answer(
                        "😔 Произошла ошибка. Попробуйте ещё раз или напишите /start"
                    )
                elif isinstance(event, CallbackQuery):
                    await event.answer(
                        "😔 Произошла ошибка. Попробуйте ещё раз.",
                        show_alert=True,
                    )
            except Exception:
                pass  # Can't send error message
            
            return None

