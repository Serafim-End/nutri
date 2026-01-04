"""
FSM State Storage using PostgreSQL
Persists bot conversation states across restarts.
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional, Union

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StorageKey

import asyncpg


logger = logging.getLogger(__name__)


class PostgresFSMStorage(BaseStorage):
    """
    PostgreSQL-based FSM storage.
    Stores state and data in the 'bot_states' table.
    
    Table schema:
    - telegram_user_id: BIGINT PRIMARY KEY
    - state: VARCHAR(255)
    - data: JSONB
    - updated_at: TIMESTAMP
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Initialize database connection pool and create table if needed."""
        if self.pool is not None:
            return
        
        logger.info("Connecting to PostgreSQL for FSM storage...")
        
        # Parse URL for asyncpg (convert postgresql+psycopg2:// to postgresql://)
        db_url = self.database_url
        if "+psycopg2" in db_url:
            db_url = db_url.replace("+psycopg2", "")
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        
        self.pool = await asyncpg.create_pool(
            db_url,
            min_size=1,
            max_size=5,
        )
        
        # Create table if not exists
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS bot_states (
                    telegram_user_id BIGINT PRIMARY KEY,
                    chat_id BIGINT NOT NULL DEFAULT 0,
                    state VARCHAR(255),
                    data JSONB DEFAULT '{}',
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Create index on updated_at for cleanup queries
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_bot_states_updated_at 
                ON bot_states (updated_at)
            """)
        
        logger.info("FSM storage connected and table ensured")
    
    async def close(self):
        """Close database connection pool."""
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
            logger.info("FSM storage connection closed")
    
    def _make_key(self, key: StorageKey) -> tuple[int, int]:
        """Convert StorageKey to (user_id, chat_id) tuple."""
        return (key.user_id, key.chat_id)
    
    async def set_state(self, key: StorageKey, state: Optional[Union[State, str]] = None) -> None:
        """Set FSM state for user."""
        user_id, chat_id = self._make_key(key)
        state_str = state.state if isinstance(state, State) else state
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO bot_states (telegram_user_id, chat_id, state, updated_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (telegram_user_id) DO UPDATE SET
                    state = $3,
                    chat_id = $2,
                    updated_at = $4
            """, user_id, chat_id, state_str, datetime.utcnow())
    
    async def get_state(self, key: StorageKey) -> Optional[str]:
        """Get FSM state for user."""
        user_id, _ = self._make_key(key)
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT state FROM bot_states WHERE telegram_user_id = $1",
                user_id,
            )
            return row["state"] if row else None
    
    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        """Set FSM data for user."""
        user_id, chat_id = self._make_key(key)
        data_json = json.dumps(data)
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO bot_states (telegram_user_id, chat_id, data, updated_at)
                VALUES ($1, $2, $3::jsonb, $4)
                ON CONFLICT (telegram_user_id) DO UPDATE SET
                    data = $3::jsonb,
                    chat_id = $2,
                    updated_at = $4
            """, user_id, chat_id, data_json, datetime.utcnow())
    
    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        """Get FSM data for user."""
        user_id, _ = self._make_key(key)
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT data FROM bot_states WHERE telegram_user_id = $1",
                user_id,
            )
            if row and row["data"]:
                return json.loads(row["data"]) if isinstance(row["data"], str) else row["data"]
            return {}
    
    async def update_data(self, key: StorageKey, data: dict[str, Any]) -> dict[str, Any]:
        """Update FSM data for user (merge with existing)."""
        current_data = await self.get_data(key)
        current_data.update(data)
        await self.set_data(key, current_data)
        return current_data
    
    async def clear_state(self, key: StorageKey) -> None:
        """Clear state and data for user."""
        user_id, _ = self._make_key(key)
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM bot_states WHERE telegram_user_id = $1",
                user_id,
            )
    
    async def cleanup_old_states(self, days: int = 30) -> int:
        """
        Clean up old states (older than N days).
        Returns number of deleted rows.
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM bot_states 
                WHERE updated_at < NOW() - INTERVAL '%s days'
            """ % days)
            # Extract count from "DELETE N"
            count = int(result.split()[-1]) if result else 0
            logger.info(f"Cleaned up {count} old FSM states (older than {days} days)")
            return count

