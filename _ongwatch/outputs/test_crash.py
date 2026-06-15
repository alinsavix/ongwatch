"""Test-only output that raises on send() after a configurable number of successes.

Not in OUTPUT_LIST; enable explicitly with --enable-output test_crash.

Use this to exercise the dispatcher's exception-handling and retry logic
without needing a real output configured.
"""
from __future__ import annotations

import logging
from typing import Any

from ..events import OngwatchEvent
from . import SendStatus

_CRASH_AFTER: int = 3


def validate_config(config: dict[str, Any]) -> None:
    unknown = sorted(set(config) - {"crash_after"})
    if unknown:
        raise ValueError(f"unknown test_crash config key(s): {', '.join(unknown)}")
    if "crash_after" in config:
        value = config["crash_after"]
        if isinstance(value, bool):
            raise ValueError("test_crash config value 'crash_after' must be an integer")
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "test_crash config value 'crash_after' must be an integer"
            ) from exc
        if parsed < 0:
            raise ValueError("test_crash config value 'crash_after' must be >= 0")


class TestCrashOutput:
    """Handles the first ``crash_after`` events then raises on every subsequent send()."""

    def __init__(
        self,
        crash_after: int = _CRASH_AFTER,
        logger: logging.Logger | None = None,
    ) -> None:
        self._crash_after = crash_after
        self._send_count = 0
        self._log = logger or logging.getLogger("test_crash")

    async def start(self) -> None:
        self._log.info(
            "test_crash output starting; will raise on send() after %d event(s)",
            self._crash_after,
        )

    async def stop(self) -> None:
        pass

    async def send(self, event: OngwatchEvent) -> SendStatus:
        self._send_count += 1
        if self._send_count > self._crash_after:
            raise RuntimeError(
                f"test_crash: simulated output failure on send #{self._send_count}"
            )
        return SendStatus.HANDLED

    async def heartbeat(self) -> None:
        pass


def create(config: dict[str, Any], logger: logging.Logger) -> TestCrashOutput:
    """Factory called by ongwatch.py when loading outputs from ongwatch.conf."""
    return TestCrashOutput(
        crash_after=int(config.get("crash_after", _CRASH_AFTER)),
        logger=logger,
    )
