from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import IO

import pytz

from ..events import (CashSupportEvent, GiftSubEvent, HypeTrainEvent,
                      OngwatchEvent, RaffleWinEvent, RaidEvent,
                      SongRequestEvent, StreamStateEvent, SubscriptionEvent)
from . import SendStatus

_EASTERN = pytz.timezone("US/Eastern")

# Dollar value per normalized subscription tier (1/2/3)
_TIER_VALUES = {1: 5.00, 2: 10.00, 3: 25.00}


def _format_ts(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_EASTERN).strftime("%Y-%m-%d %H:%M:%S")


def _support_line(
    dt: datetime,
    gifter: str = "",
    supporter: str = "",
    support_type: str = "",
    amount: float = 0.0,
    comment: str = "",
) -> str:
    """Build a tab-separated line matching the historical printsupport() format."""
    ts_str = _format_ts(dt)
    return f"{ts_str}\t\t{gifter}\t{supporter}\t{support_type}\t${amount:0.2f}\tna\t{comment}"


class BumpLogOutput:
    def __init__(self, path: str) -> None:
        self._path = path
        self._file: IO[str] | None = None

    async def start(self) -> None:
        if self._path in ("-", "stdout"):
            self._file = sys.stdout
        else:
            self._file = open(self._path, "a", encoding="utf-8")

    async def stop(self) -> None:
        if self._file is not None and self._file is not sys.stdout:
            self._file.close()
        self._file = None

    def _write(self, line: str) -> None:
        assert self._file is not None
        self._file.write(line + "\n")
        self._file.flush()

    async def heartbeat(self) -> None:
        ts = datetime.now(tz=timezone.utc).isoformat()
        self._write(f"# heartbeat {ts}")

    async def send(self, event: OngwatchEvent) -> SendStatus:
        assert self._file is not None

        if isinstance(event, CashSupportEvent):
            kind_to_type = {"bits": "Bits", "tip": "Tip", "donation": "Tip"}
            support_type = kind_to_type.get(event.kind, event.kind.capitalize())
            self._write(_support_line(
                event.timestamp,
                supporter=event.username,
                support_type=support_type,
                amount=event.amount,
                comment=event.comment or "",
            ))
            return SendStatus.HANDLED

        if isinstance(event, SubscriptionEvent):
            support_type = f"Sub #{event.months}" if event.months else "Sub"
            amount = _TIER_VALUES.get(event.tier, 5.00)
            self._write(_support_line(
                event.timestamp,
                supporter=event.username,
                support_type=support_type,
                amount=amount,
                comment=event.message or "",
            ))
            return SendStatus.HANDLED

        if isinstance(event, GiftSubEvent):
            gifter = event.gifter or "AnAnonymousGifter"
            amount = _TIER_VALUES.get(event.tier, 5.00)
            for recipient in event.recipients:
                self._write(_support_line(
                    event.timestamp,
                    gifter=gifter,
                    supporter=recipient,
                    support_type="Sub",
                    amount=amount,
                ))
            return SendStatus.HANDLED

        if isinstance(event, RaidEvent):
            self._write(_support_line(
                event.timestamp,
                supporter=event.from_channel,
                support_type=f"Raid - {event.viewer_count}",
            ))
            return SendStatus.HANDLED

        if isinstance(event, RaffleWinEvent):
            self._write(_support_line(
                event.timestamp,
                supporter=event.winner,
                support_type="Raffle",
            ))
            return SendStatus.HANDLED

        if isinstance(event, StreamStateEvent):
            ts_str = _format_ts(event.timestamp)
            label = "ONLINE" if event.state == "online" else "OFFLINE"
            self._write(f"{ts_str}  === {label} ===")
            return SendStatus.HANDLED

        if isinstance(event, HypeTrainEvent):
            ts_str = _format_ts(event.timestamp)
            if event.kind == "begin":
                self._write(f"{ts_str}  === HYPE TRAIN BEGIN ===")
            else:
                self._write(
                    f"{ts_str}  === HYPE TRAIN END"
                    f" (level={event.level}, total={event.total}) ==="
                )
            return SendStatus.HANDLED

        if isinstance(event, SongRequestEvent):
            requester = event.requester or "unknown"
            self._write(f"  SONG REQUEST FROM {requester}: {event.title}")
            return SendStatus.HANDLED

        return SendStatus.REJECTED
