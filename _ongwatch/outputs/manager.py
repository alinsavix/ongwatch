import argparse
import asyncio
import importlib
import inspect
import logging
import os
import pkgutil
from typing import Any, Dict, List, Optional, Type

from _ongwatch.outputs.base import OutputHandler
from _ongwatch.util import get_credentials


class OutputManager:
    handlers: List[OutputHandler]
    initialized: bool = False

    def __init__(self) -> None:
        self.handlers = []
        self.initialized = False
        self.logger = logging.getLogger("output.manager")

    async def initialize(self, args: argparse.Namespace, enabled_outputs: list[str]) -> None:
        if self.initialized:
            return

        # Discover and load all output handlers
        # FIXME: Can we pass them just their own config? Do we want to?
        # FIXME: We're passing the same arguments like 4 layers deep, this
        # probably means we have an abstraction failure.
        await self._load_handlers(args, enabled_outputs)

        # Initialize all handlers, wait for all of the inits to complete
        init_tasks = [handler.initialize() for handler in self.handlers]
        await asyncio.gather(*init_tasks)

        self.initialized = True

    async def _load_handlers(self, args: argparse.Namespace, enabled_outputs: list[str]) -> None:
        import _ongwatch.outputs as outputs

        # Find all packages in the outputs package
        for _, name, is_pkg in pkgutil.iter_modules(outputs.__path__, outputs.__name__ + '.'):
            if not is_pkg or name == '_ongwatch.outputs.base' or name == '_ongwatch.outputs.manager':
                self.logger.debug(f"Skipping non-output-handler package: {name}")
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
                    handler_config = get_credentials(args.credentials_file, handler_name, args.environment)

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
            raise RuntimeError("OutputManager not initialized")

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
