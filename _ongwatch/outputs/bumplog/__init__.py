import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from _ongwatch.outputs.base import OutputHandler

import aiofiles


class BumpLogHandler(OutputHandler):
    """Output handler that writes one line to a log file for each event."""

    logger: logging.Logger
    log_file: Path
    log_dir: Path
    log_path: Path

    # FIXME: should probably be async?
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.log_file = Path(self.config.get('log_file', 'bump.log'))
        self.log_dir = Path(self.config.get('log_dir', '.'))
        self.log_path = self.log_dir / self.log_file if self.log_dir else self.log_file
        self.lock = asyncio.Lock()

        self.logger = logging.getLogger("output.bumplog")
        self.logger.error("ONG BUMPLOG")

    async def initialize(self) -> None:
        """Ensure the log directory exists."""
        if self.log_dir and not self.log_dir.exists():
            self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create the file if it doesn't exist
        if not self.log_path.exists():
            async with self.lock:
                async with aiofiles.open(self.log_path, mode='w') as f:
                    await f.write(f"# BumpLog started at {datetime.now().isoformat()}\n")

    async def handle_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Write a single line to the log file for the event."""
        timestamp = datetime.now().isoformat()
        log_line = f"{timestamp} | {event_type} | {data}\n"

        async with self.lock:
            async with aiofiles.open(self.log_path, mode='a') as f:
                await f.write(log_line)

    async def shutdown(self) -> None:
        """Close the log file."""
        if self.log_path.exists():
            async with self.lock:
                async with aiofiles.open(self.log_path, mode='a') as f:
                    await f.write(f"# BumpLog ended at {datetime.now().isoformat()}\n")
