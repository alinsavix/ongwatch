import asyncio
import importlib
import inspect
import logging
import os
import pkgutil
from typing import Any, Dict, List, Optional, Type

from _ongwatch.outputs.base import OutputHandler


class OutputManager:
    """Manages all output handlers and dispatches events to them."""
    handlers: List[OutputHandler]
    initialized: bool = False

    def __init__(self) -> None:
        self.handlers = []
        self.initialized = False
        self.logger = logging.getLogger("output.manager")

    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize all output handlers."""
        if self.initialized:
            return

        config = config or {}

        # Discover and load all output handlers
        await self._load_handlers(config)

        # Initialize all handlers
        init_tasks = [handler.initialize() for handler in self.handlers]
        await asyncio.gather(*init_tasks)

        self.initialized = True

    async def _load_handlers(self, config: Dict[str, Any]) -> None:
        """Discover and load all output handlers from the outputs package."""
        import _ongwatch.outputs as outputs

        # Find all packages in the outputs package
        for _, name, is_pkg in pkgutil.iter_modules(outputs.__path__, outputs.__name__ + '.'):
            if not is_pkg or name == '_ongwatch.outputs.base' or name == '_ongwatch.outputs.manager':
                continue

            self.logger.debug(f"Initializing output handler package: {name}")

            # Import the package
            module = importlib.import_module(name)

            # Find all OutputHandler subclasses in the module
            for _, item in inspect.getmembers(module, inspect.isclass):
                if (issubclass(item, OutputHandler)
                        and item is not OutputHandler
                        and item.__module__ == name):
                    # Get handler-specific config
                    handler_name = item.__name__
                    handler_config = config.get(handler_name, {})

                    self.logger.info(f"Initializing output handler: {handler_name}")

                    # Create an instance of the handler
                    handler = item(handler_config)
                    self.handlers.append(handler)
                else:
                    self.logger.debug(f"Skipping non-output-handler class: {item}")

    # dispatch to all registered handlers
    async def dispatch(self, event_type: str, data: Dict[str, Any]) -> None:
        # FIXME: should we just raise an exception rather than initializing?
        if not self.initialized:
            await self.initialize()

        # Create tasks for each handler
        tasks = []
        for handler in self.handlers:
            logging.getLogger("DISPATCH").info(f"Dispatching event: {event_type} to {handler.name}")
            task = asyncio.create_task(
                handler.handle_event(event_type, data),
                name=f"{handler.name}_{event_type}"
            )
            tasks.append(task)

        # Wait for all handlers to process the event
        await asyncio.gather(*tasks, return_exceptions=True)

    async def shutdown(self) -> None:
        # FIXME: should we just raise an exception?
        if not self.initialized:
            return

        shutdown_tasks = [handler.shutdown() for handler in self.handlers]
        await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        self.initialized = False
