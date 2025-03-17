from typing import Any, Dict, Optional

from _ongwatch.outputs.base import OutputHandler
from _ongwatch.outputs.manager import OutputManager

# Singleton instance of the output manager
_output_manager = None

def get_output_manager() -> OutputManager:
    """Get the singleton instance of the output manager."""
    global _output_manager
    if _output_manager is None:
        _output_manager = OutputManager()
    return _output_manager

async def initialize_outputs(config: Optional[Dict[str, Any]] = None) -> OutputManager:
    """Initialize the output system with the given configuration."""
    manager = get_output_manager()
    await manager.initialize(config)
    return manager

async def dispatch_event(event_type: str, data: Dict[str, Any]) -> None:
    """Dispatch an event to all registered output handlers."""
    manager = get_output_manager()
    await manager.dispatch(event_type, data)

# Export the base class for type hints
__all__ = ['OutputHandler', 'get_output_manager', 'initialize_outputs', 'dispatch_event']
