from __future__ import annotations

import importlib
from enum import Enum
from types import ModuleType
from typing import Protocol

from ..events import OngwatchEvent


class SendStatus(Enum):
    HANDLED   = "handled"    # delivered successfully
    REJECTED  = "rejected"   # wrong type for this output, intentionally ignored
    TRANSIENT = "transient"  # couldn't deliver right now, please retry
    ERROR     = "error"      # something is wrong, do not retry this event


class Output(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def send(self, event: OngwatchEvent) -> SendStatus: ...
    async def heartbeat(self) -> None: ...


OUTPUT_LIST = ["bumplog", "console", "mqtt", "sqlite"]


def get_output(name: str) -> ModuleType:
    return importlib.import_module(f"_ongwatch.outputs.{name}")
