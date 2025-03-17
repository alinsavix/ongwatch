from typing import Any, Dict, Optional

import asyncpg

from .base import OutputHandler


class DatabaseHandler(OutputHandler):
    """Output handler that stores events in a PostgreSQL database."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.connection_string = self.config.get('connection_string', '')
        self.table_name = self.config.get('table_name', 'events')
        self.pool = None

    async def initialize(self) -> None:
        """Initialize the database connection pool."""
        self.pool = await asyncpg.create_pool(self.connection_string)

    async def handle_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Store the event in the database."""
        if not self.pool:
            return

        async with self.pool.acquire() as conn:
            await conn.execute(
                f"INSERT INTO {self.table_name} (event_type, data) VALUES ($1, $2)",
                event_type, data
            )

    async def shutdown(self) -> None:
        """Close the database connection pool."""
        if self.pool:
            await self.pool.close()
