"""Test-only backend that crashes after a short delay.

Not in BACKEND_LIST; enable explicitly with --enable-backend test_crash.

Use this to exercise the backend supervisor's backoff and restart logic
without needing a live Twitch/StreamElements/StreamLabs connection.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
from typing import Any, Dict

from ..dispatcher import Dispatcher

# Seconds to run before crashing.  Short enough to see multiple restart
# cycles within the supervisor's 5-minute window.
_CRASH_AFTER: float = 3.0


async def start(
    args: argparse.Namespace,
    creds: Dict[str, Any] | None,
    logger: logging.Logger,
    dispatcher: Dispatcher,
) -> None:
    logger.info("test_crash backend starting; will crash in %.1fs", _CRASH_AFTER)
    await asyncio.sleep(_CRASH_AFTER)
    raise RuntimeError("test_crash: simulated backend failure")
