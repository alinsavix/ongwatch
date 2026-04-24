from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import IO, Any

import pytz

from ..events import (CashSupportEvent, GiftSubEvent, HypeTrainEvent,
                      OngwatchEvent, RaffleWinEvent, RaidEvent,
                      SongRequestEvent, StreamStateEvent, SubscriptionEvent)
from . import SendStatus

_EASTERN = pytz.timezone("US/Eastern")
_TIER_NAMES = {1: "Tier 1", 2: "Tier 2", 3: "Tier 3"}


def _ts(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_EASTERN).strftime("%H:%M:%S")


class ConsoleOutput:
    def __init__(self, stream: IO[str] | None = None) -> None:
        self._stream = stream or sys.stdout

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    def _write(self, line: str, is_test: bool = False) -> None:
        if is_test:
            line += " [test]"
        self._stream.write(line + "\n")
        self._stream.flush()

    async def heartbeat(self) -> None:
        pass  # no-op: console needs no health-check side-effect

    async def send(self, event: OngwatchEvent) -> SendStatus:
        ts = _ts(event.timestamp)

        if isinstance(event, CashSupportEvent):
            if event.kind == "bits":
                bits = int(event.amount * 100)
                msg = f"[{ts}] BITS    {event.username} cheered {bits} bits (${event.amount:.2f})"
                if event.comment:
                    msg += f": {event.comment}"
            else:
                kind_label = "TIP" if event.kind in ("tip", "donation") else event.kind.upper()
                msg = f"[{ts}] {kind_label:<7} {event.username} tipped ${event.amount:.2f}"
                if event.comment:
                    msg += f": {event.comment}"
            self._write(msg, event.is_test)
            return SendStatus.HANDLED

        if isinstance(event, SubscriptionEvent):
            tier = _TIER_NAMES.get(event.tier, f"Tier {event.tier}")
            action = "resubscribed" if event.is_resub else "subscribed"
            month_str = f", month #{event.months}" if event.months else ""
            msg = f"[{ts}] SUB     {event.username} {action} ({tier}{month_str})"
            if event.message:
                msg += f": {event.message}"
            self._write(msg, event.is_test)
            return SendStatus.HANDLED

        if isinstance(event, GiftSubEvent):
            tier = _TIER_NAMES.get(event.tier, f"Tier {event.tier}")
            gifter = event.gifter
            if len(event.recipients) == 1:
                msg = (
                    f"[{ts}] GIFT    {gifter} gifted {event.recipients[0]}"
                    f" a {tier} sub"
                )
            else:
                names = ", ".join(event.recipients)
                msg = (
                    f"[{ts}] GIFT    {gifter} gifted {len(event.recipients)}"
                    f" {tier} subs: {names}"
                )
            self._write(msg, event.is_test)
            return SendStatus.HANDLED

        if isinstance(event, RaidEvent):
            self._write(
                f"[{ts}] RAID    {event.from_channel} raided"
                f" with {event.viewer_count} viewers",
                event.is_test,
            )
            return SendStatus.HANDLED

        if isinstance(event, RaffleWinEvent):
            self._write(f"[{ts}] RAFFLE  {event.winner} won the raffle", event.is_test)
            return SendStatus.HANDLED

        if isinstance(event, StreamStateEvent):
            label = "ONLINE" if event.state == "online" else "OFFLINE"
            self._write(f"[{ts}] === {label} ===", event.is_test)
            return SendStatus.HANDLED

        if isinstance(event, HypeTrainEvent):
            if event.kind == "begin":
                self._write(f"[{ts}] === HYPE TRAIN BEGIN ===", event.is_test)
            else:
                self._write(
                    f"[{ts}] === HYPE TRAIN END"
                    f" (level={event.level}, total={event.total}) ===",
                    event.is_test,
                )
            return SendStatus.HANDLED

        if isinstance(event, SongRequestEvent):
            requester = event.requester or "unknown"
            self._write(f'[{ts}] SONG REQUEST from {requester}: "{event.title}"', event.is_test)
            return SendStatus.HANDLED

        return SendStatus.REJECTED


def create(config: dict[str, Any]) -> ConsoleOutput:
    """Factory called by ongwatch.py when loading outputs from ongwatch.conf."""
    return ConsoleOutput()
