"""
Output handler plugin system for ongwatch.

This module provides the plugin infrastructure for output handlers,
mirroring the pattern used for backend plugins.
"""

import argparse
import asyncio
import importlib
import logging
from types import ModuleType
from typing import Callable, Coroutine, Dict, Optional

from _ongwatch.event import Event

# Type alias for output handler start function
OutputStartHandler = Callable[
    [argparse.Namespace, Optional[Dict[str, str]], logging.Logger, asyncio.Queue[Event]],
    Coroutine[None, None, None]
]

# List of available output handlers
OUTPUT_LIST = ["bumplog"]


def output_list() -> list[str]:
    """Return list of available output handler names"""
    return OUTPUT_LIST


def get_output(name: str) -> ModuleType:
    """
    Dynamically import and return output handler module.

    Args:
        name: Name of output handler (e.g., "bumplog", "mqtt")

    Returns:
        Module object containing start() function

    Raises:
        ModuleNotFoundError: If handler doesn't exist
    """
    return importlib.import_module(f"_ongwatch.outputs.{name}")
