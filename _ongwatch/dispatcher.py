"""
Event dispatcher for ongwatch output handlers.

The dispatcher maintains queues for each output handler and distributes
events to all active handlers. Each handler processes events independently
at its own pace.
"""

import asyncio
import copy
import logging
from typing import Dict, Optional

from _ongwatch.event import Event

# Default maximum queue size for output handlers
DEFAULT_QUEUE_SIZE = 100


class EventDispatcher:
    """
    Singleton dispatcher that distributes events to all registered output handlers.

    The dispatcher maintains a bounded queue for each output handler and
    broadcasts events to all queues. If a queue is full, the oldest event
    is dropped to make room for the new one.
    """

    _instance: Optional['EventDispatcher'] = None
    _initialized: bool = False

    def __new__(cls) -> 'EventDispatcher':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Only initialize once (singleton pattern)
        if self._initialized:
            return

        self.logger = logging.getLogger("dispatcher")
        self.output_queues: Dict[str, asyncio.Queue[Event]] = {}
        self.queue_size = DEFAULT_QUEUE_SIZE
        self.stats: Dict[str, Dict[str, int]] = {}  # Track events dispatched/dropped per output
        self._initialized = True

    def register_output(self, name: str, queue_size: Optional[int] = None) -> asyncio.Queue[Event]:
        """
        Register an output handler and create its event queue.

        Args:
            name: Output handler name (e.g., "bumplog", "mqtt")
            queue_size: Maximum queue size (default: DEFAULT_QUEUE_SIZE)

        Returns:
            Event queue for this output handler
        """
        if name in self.output_queues:
            self.logger.warning(f"Output '{name}' already registered, returning existing queue")
            return self.output_queues[name]

        size = queue_size if queue_size is not None else self.queue_size
        queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=size)
        self.output_queues[name] = queue
        self.stats[name] = {"dispatched": 0, "dropped": 0}

        self.logger.info(f"Registered output handler '{name}' with queue size {size}")
        return queue

    def unregister_output(self, name: str) -> None:
        """Unregister an output handler (for cleanup)"""
        if name in self.output_queues:
            del self.output_queues[name]
            self.logger.info(f"Unregistered output handler '{name}'")

    async def dispatch_event(self, event: Event) -> None:
        """
        Dispatch event to all registered output handlers.

        Each handler receives a copy of the event. If a handler's queue is full,
        the oldest event is dropped to make room for the new one.

        Args:
            event: Event to dispatch
        """
        if not self.output_queues:
            self.logger.debug("No output handlers registered, dropping event")
            return

        self.logger.debug(f"Dispatching {event.event_type.value} event to {len(self.output_queues)} handlers")

        for name, queue in self.output_queues.items():
            try:
                # Make a copy for each handler to prevent modification issues
                event_copy = copy.deepcopy(event)

                # If queue is full, drop oldest event to make room
                if queue.full():
                    try:
                        dropped = queue.get_nowait()
                        queue.task_done()
                        self.stats[name]["dropped"] += 1
                        self.logger.warning(
                            f"Output '{name}' queue full, dropped {dropped.event_type.value} event"
                        )
                    except asyncio.QueueEmpty:
                        pass

                # Add new event
                queue.put_nowait(event_copy)
                self.stats[name]["dispatched"] += 1

            except Exception as e:
                self.logger.error(f"Error dispatching to '{name}': {e}", exc_info=True)

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """Return dispatcher statistics"""
        return self.stats.copy()


# Global dispatcher instance
_dispatcher: Optional[EventDispatcher] = None


def get_dispatcher() -> EventDispatcher:
    """Get the global event dispatcher instance"""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = EventDispatcher()
    return _dispatcher
