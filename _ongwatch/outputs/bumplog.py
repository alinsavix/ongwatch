from __future__ import annotations

import logging
import os
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from typing import IO, Any

import pytz

from ..events import (CashSupportEvent, GiftSubEvent, HypeTrainEvent,
                      OngwatchEvent, RaffleWinEvent, RaidIncomingEvent,
                      RaidOutgoingEvent, SongRequestEvent, StreamStateEvent,
                      SubscriptionEvent)
from . import SendStatus

_EASTERN = pytz.timezone("US/Eastern")

# Value in cents per normalized subscription tier (1/2/3)
_TIER_VALUES_CENTS = {1: 500, 2: 1000, 3: 2500}


def validate_config(config: dict[str, Any]) -> None:
    unknown = sorted(set(config) - {"path"})
    if unknown:
        raise ValueError(f"unknown bumplog config key(s): {', '.join(unknown)}")
    if "path" in config:
        path = config["path"]
        if not isinstance(path, str):
            raise ValueError("bumplog config value 'path' must be a string")
        if not path:
            raise ValueError("bumplog config value 'path' cannot be empty")


def _format_ts(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_EASTERN).strftime("%Y-%m-%d %H:%M:%S")


def _support_line(
    dt: datetime,
    gifter: str | None = "",
    supporter: str = "",
    support_type: str = "",
    amount_cents: int = 0,
    comment: str = "",
) -> str:
    """Build a tab-separated line matching the historical printsupport() format."""
    ts_str = _format_ts(dt)
    dollars = amount_cents / 100
    return f"{ts_str}\t\t{gifter}\t{supporter}\t{support_type}\t${dollars:0.2f}\tna\t{comment}"


# ---------------------------------------------------------------------------
# Per-event-type formatters. Each returns the bump-log line(s) to write (gift
# subs expand to one line per recipient). To support a new event type, add a
# formatter and a row in _FORMATTERS; unhandled types are REJECTED.
# ---------------------------------------------------------------------------

def _cash_lines(event: CashSupportEvent) -> list[str]:
    kind_to_type = {"bits": "Bits", "tip": "Tip", "donation": "Tip"}
    support_type = kind_to_type.get(event.kind, event.kind.capitalize())
    return [_support_line(
        event.timestamp,
        supporter=event.username,
        support_type=support_type,
        amount_cents=event.amount_cents,
        comment=event.comment or "",
    )]


def _sub_lines(event: SubscriptionEvent) -> list[str]:
    support_type = f"Sub #{event.months}" if event.months else "Sub"
    amount_cents = _TIER_VALUES_CENTS.get(event.tier, 500)
    return [_support_line(
        event.timestamp,
        supporter=event.username,
        support_type=support_type,
        amount_cents=amount_cents,
        comment=event.message or "",
    )]


def _giftsub_lines(event: GiftSubEvent) -> list[str]:
    amount_cents = _TIER_VALUES_CENTS.get(event.tier, 500)
    return [
        _support_line(
            event.timestamp,
            gifter=event.gifter,
            supporter=recipient,
            support_type="Sub",
            amount_cents=amount_cents,
        )
        for recipient in event.recipients
    ]


def _raid_incoming_lines(event: RaidIncomingEvent) -> list[str]:
    return [_support_line(
        event.timestamp,
        supporter=event.from_channel,
        support_type=f"Raid - {event.viewer_count}",
    )]


def _raid_outgoing_lines(event: RaidOutgoingEvent) -> list[str]:
    return [_support_line(
        event.timestamp,
        supporter=event.to_channel,
        support_type=f"Raid Out - {event.viewer_count}",
    )]


def _raffle_lines(event: RaffleWinEvent) -> list[str]:
    return [_support_line(
        event.timestamp,
        supporter=event.winner,
        support_type="Raffle",
    )]


def _stream_state_lines(event: StreamStateEvent) -> list[str]:
    ts_str = _format_ts(event.timestamp)
    label = "ONLINE" if event.state == "online" else "OFFLINE"
    return [f"{ts_str}  === {label} ==="]


def _hype_train_lines(event: HypeTrainEvent) -> list[str]:
    ts_str = _format_ts(event.timestamp)
    if event.kind == "begin":
        return [f"{ts_str}  === HYPE TRAIN BEGIN ==="]
    return [
        f"{ts_str}  === HYPE TRAIN END"
        f" (level={event.level}, total={event.total}) ==="
    ]


def _song_request_lines(event: SongRequestEvent) -> list[str]:
    requester = event.requester or "unknown"
    return [f"  SONG REQUEST FROM {requester}: {event.title}"]


_FORMATTERS: dict[type[OngwatchEvent], Callable[[Any], list[str]]] = {
    CashSupportEvent:  _cash_lines,
    SubscriptionEvent: _sub_lines,
    GiftSubEvent:      _giftsub_lines,
    RaidIncomingEvent: _raid_incoming_lines,
    RaidOutgoingEvent: _raid_outgoing_lines,
    RaffleWinEvent:    _raffle_lines,
    StreamStateEvent:  _stream_state_lines,
    HypeTrainEvent:    _hype_train_lines,
    SongRequestEvent:  _song_request_lines,
}


class BumpLogOutput:
    def __init__(self, path: str, logger: logging.Logger | None = None) -> None:
        self._path = path
        self._file: IO[str] | None = None
        self._log = logger or logging.getLogger("bumplog")

    async def start(self) -> None:
        if self._path in ("-", "stdout"):
            self._file = sys.stdout
            self._log.info("bumplog output writing to stdout")
        else:
            self._file = open(self._path, "a", encoding="utf-8")
            self._log.info("bumplog output writing to %s", self._path)

    async def stop(self) -> None:
        if self._file is not None and self._file is not sys.stdout:
            self._file.close()
        self._file = None

    def _write(self, line: str) -> None:
        assert self._file is not None
        self._file.write(line + "\n")
        self._file.flush()

    async def heartbeat(self) -> None:
        # Health-check without mutating the data file: verify our handle is
        # still open and the path is still writable.
        if self._file is None or self._file.closed:
            raise RuntimeError(f"bumplog file {self._path!r} is not open")
        if self._file is sys.stdout:
            return
        if not os.access(self._path, os.W_OK):
            raise RuntimeError(f"bumplog file {self._path!r} is not writable")
        self._log.debug("heartbeat ok: %s is writable", self._path)

    async def send(self, event: OngwatchEvent) -> SendStatus:
        assert self._file is not None

        if event.is_test:
            return SendStatus.REJECTED

        formatter = _FORMATTERS.get(type(event))
        if formatter is None:
            self._log.debug("rejecting unhandled event type %s", type(event).__name__)
            return SendStatus.REJECTED

        for line in formatter(event):
            self._write(line)
        return SendStatus.HANDLED


def create(config: dict[str, Any], logger: logging.Logger) -> BumpLogOutput:
    """Factory called by ongwatch.py when loading outputs from ongwatch.conf."""
    return BumpLogOutput(path=config.get("path", "-"), logger=logger)
