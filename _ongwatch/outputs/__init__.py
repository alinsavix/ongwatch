import argparse
import importlib
from types import ModuleType
from typing import Any, Dict, Optional

from _ongwatch.outputs.base import OutputHandler
from _ongwatch.outputs.manager import OutputManager

OUTPUT_LIST = ["bumplog", "mqtt"]

def output_list() -> list[str]:
    return OUTPUT_LIST

# FIXME: Should we return the import, or should we return specific functions?
def get_output(name: str) -> ModuleType:
    return importlib.import_module(f"_ongwatch.outputs.{name}")

# Singleton instance of the output manager
_output_manager = None

def get_output_manager() -> OutputManager:
    """Get the singleton instance of the output manager."""
    global _output_manager
    if _output_manager is None:
        _output_manager = OutputManager()
    return _output_manager

async def initialize_outputs(args: argparse.Namespace, enabled_outputs: list[str]) -> OutputManager:
    manager = get_output_manager()
    await manager.initialize(args, enabled_outputs)
    return manager

async def dispatch_event(event_type: str, data: Dict[str, Any]) -> None:
    """Dispatch an event to all registered output handlers."""
    manager = get_output_manager()
    await manager.dispatch(event_type, data)

# Export the base class for type hints
__all__ = ['OutputHandler', 'get_output_manager', 'initialize_outputs', 'dispatch_event']
