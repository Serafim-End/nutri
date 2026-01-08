"""
Bot Handlers Package
"""

from aiogram import Router

from .start import router as start_router
from .menu import router as menu_router
from .profile import router as profile_router
from .services import router as services_router
from .cabinet import router as cabinet_router
from .schedule import router as schedule_router
from .debug import router as debug_router


def get_all_routers() -> list[Router]:
    """Get all handler routers."""
    return [
        start_router,
        menu_router,
        profile_router,
        services_router,
        cabinet_router,
        schedule_router,
        debug_router,
    ]

