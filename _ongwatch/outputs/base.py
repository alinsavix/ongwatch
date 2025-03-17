import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class OutputHandler(ABC):
    """Base class for all output handlers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.name = self.__class__.__name__

    @abstractmethod
    async def handle_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Process an event with the given type and data."""
        pass

    async def initialize(self) -> None:
        """Initialize the output handler. Override if needed."""
        pass

    async def shutdown(self) -> None:
        """Clean up resources. Override if needed."""
        pass
