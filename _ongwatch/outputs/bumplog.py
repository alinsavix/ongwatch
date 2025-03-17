import asyncio
import os
from datetime import datetime
from typing import Any, Dict, Optional

from _ongwatch.outputs.base import OutputHandler


class BumpLogHandler(OutputHandler):
    """Output handler that writes one line to a log file for each event."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.log_file = self.config.get('log_file', 'bumplog.log')
        self.log_dir = self.config.get('log_dir', '')
        self.log_path = os.path.join(self.log_dir, self.log_file) if self.log_dir else self.log_file
        self.lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Ensure the log directory exists."""
        if self.log_dir and not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

        # Create the file if it doesn't exist
        if not os.path.exists(self.log_path):
            async with self.lock:
                with open(self.log_path, 'w') as f:
                    f.write(f"# BumpLog started at {datetime.now().isoformat()}\n")

    async def handle_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Write a single line to the log file for the event."""
        timestamp = datetime.now().isoformat()
        log_line = f"{timestamp} | {event_type} | {data}\n"

        async with self.lock:
            with open(self.log_path, 'a') as f:
                f.write(log_line)
