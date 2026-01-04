"""
Main Bot Entry Point
Handles bot initialization, startup, and shutdown.
Supports both polling (dev) and webhook (prod) modes.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from config import get_config
from storage import PostgresFSMStorage
from api_client import close_api_client
from middleware import LoggingMiddleware, ThrottlingMiddleware, ErrorHandlingMiddleware
from handlers import get_all_routers


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

# Reduce noise from libraries
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("aiogram").setLevel(logging.INFO)

logger = logging.getLogger(__name__)


async def create_bot_and_dispatcher() -> tuple[Bot, Dispatcher, PostgresFSMStorage]:
    """Create and configure bot instance."""
    config = get_config()
    
    # Set log level from config
    logging.getLogger().setLevel(getattr(logging, config.log_level.upper(), logging.INFO))
    
    # Initialize bot
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    # Initialize FSM storage
    storage = PostgresFSMStorage(config.database_url)
    await storage.connect()
    
    # Initialize dispatcher
    dp = Dispatcher(storage=storage)
    
    # Register middleware
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    dp.message.middleware(ThrottlingMiddleware(rate_limit=0.3))
    dp.callback_query.middleware(ThrottlingMiddleware(rate_limit=0.3))
    dp.message.middleware(ErrorHandlingMiddleware())
    dp.callback_query.middleware(ErrorHandlingMiddleware())
    
    # Register all routers
    for router in get_all_routers():
        dp.include_router(router)
    
    logger.info("Bot and dispatcher initialized")
    
    return bot, dp, storage


async def on_startup(bot: Bot):
    """Startup hook."""
    config = get_config()
    
    # Get bot info
    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username} (id={me.id})")
    
    # Set webhook if in webhook mode
    if config.mode == "webhook":
        webhook_url = f"{config.webhook_url}{config.webhook_path}"
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
        )
        logger.info(f"Webhook set: {webhook_url}")
    else:
        # Delete webhook to use polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted, using polling mode")


async def on_shutdown(bot: Bot, storage: PostgresFSMStorage):
    """Shutdown hook."""
    logger.info("Shutting down bot...")
    
    # Close FSM storage
    await storage.close()
    
    # Close API client
    await close_api_client()
    
    # Close bot session
    await bot.session.close()
    
    logger.info("Bot shutdown complete")


async def run_polling():
    """Run bot in polling mode (for development)."""
    bot, dp, storage = await create_bot_and_dispatcher()
    
    try:
        await on_startup(bot)
        logger.info("Starting polling...")
        await dp.start_polling(bot)
    finally:
        await on_shutdown(bot, storage)


async def run_webhook():
    """Run bot in webhook mode (for production)."""
    config = get_config()
    bot, dp, storage = await create_bot_and_dispatcher()
    
    # Create aiohttp app
    app = web.Application()
    
    # Webhook handler
    async def handle_webhook(request: web.Request) -> web.Response:
        try:
            data = await request.json()
            from aiogram.types import Update
            update = Update.model_validate(data)
            await dp.feed_update(bot, update)
            return web.Response(status=200)
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return web.Response(status=500)
    
    # Health check
    async def handle_health(request: web.Request) -> web.Response:
        return web.json_response({"status": "ok", "bot": "running"})
    
    # Register routes
    app.router.add_post(config.webhook_path, handle_webhook)
    app.router.add_get("/health", handle_health)
    
    # Startup/shutdown hooks
    async def on_app_startup(app: web.Application):
        await on_startup(bot)
    
    async def on_app_shutdown(app: web.Application):
        await on_shutdown(bot, storage)
    
    app.on_startup.append(on_app_startup)
    app.on_shutdown.append(on_app_shutdown)
    
    # Run server
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(
        runner,
        host=config.webhook_host,
        port=config.webhook_port,
    )
    
    logger.info(f"Starting webhook server on {config.webhook_host}:{config.webhook_port}")
    
    await site.start()
    
    # Keep running
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


def main():
    """Main entry point."""
    try:
        config = get_config()
        logger.info(f"Starting bot in {config.mode} mode")
        
        if config.mode == "webhook":
            asyncio.run(run_webhook())
        else:
            asyncio.run(run_polling())
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Bot crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

