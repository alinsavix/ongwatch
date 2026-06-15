from __future__ import annotations

import logging
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
_TIER_NAMES = {1: "Tier 1", 2: "Tier 2", 3: "Tier 3"}


def validate_config(config: dict[str, Any]) -> None:
    unknown = sorted(config)
    if unknown:
        raise ValueError(f"unknown console config key(s): {', '.join(unknown)}")


def _ts(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_EASTERN).strftime("%H:%M:%S")


# ---------------------------------------------------------------------------
# Per-event-type formatters. Each returns the single console line to write.
# To support a new event type, add a formatter and a row in _FORMATTERS;
# unhandled types are REJECTED.
# ---------------------------------------------------------------------------

def _fmt_cash(event: CashSupportEvent) -> str:
    ts = _ts(event.timestamp)
    dollars = event.amount_cents / 100
    if event.kind == "bits":
        msg = (
            f"[{ts}] BITS    {event.username} cheered"
            f" {event.amount_cents} bits (${dollars:.2f})"
        )
        if event.comment:
            msg += f": {event.comment}"
        return msg
    kind_label = "TIP" if event.kind in ("tip", "donation") else event.kind.upper()
    msg = f"[{ts}] {kind_label:<7} {event.username} tipped ${dollars:.2f}"
    if event.comment:
        msg += f": {event.comment}"
    return msg


def _fmt_sub(event: SubscriptionEvent) -> str:
    ts = _ts(event.timestamp)
    tier = _TIER_NAMES.get(event.tier, f"Tier {event.tier}")
    action = "resubscribed" if event.is_resub else "subscribed"
    month_str = f", month #{event.months}" if event.months else ""
    msg = f"[{ts}] SUB     {event.username} {action} ({tier}{month_str})"
    if event.message:
        msg += f": {event.message}"
    return msg


def _fmt_giftsub(event: GiftSubEvent) -> str:
    ts = _ts(event.timestamp)
    tier = _TIER_NAMES.get(event.tier, f"Tier {event.tier}")
    gifter = event.gifter
    if len(event.recipients) == 1:
        return (
            f"[{ts}] GIFT    {gifter} gifted {event.recipients[0]}"
            f" a {tier} sub"
        )
    names = ", ".join(event.recipients)
    return (
        f"[{ts}] GIFT    {gifter} gifted {len(event.recipients)}"
        f" {tier} subs: {names}"
    )


def _fmt_raid_incoming(event: RaidIncomingEvent) -> str:
    ts = _ts(event.timestamp)
    return (
        f"[{ts}] RAID IN {event.from_channel} raided"
        f" with {event.viewer_count} viewers"
    )


def _fmt_raid_outgoing(event: RaidOutgoingEvent) -> str:
    ts = _ts(event.timestamp)
    return (
        f"[{ts}] RAID OUT raided {event.to_channel}"
        f" with {event.viewer_count} viewers"
    )


def _fmt_raffle(event: RaffleWinEvent) -> str:
    ts = _ts(event.timestamp)
    return f"[{ts}] RAFFLE  {event.winner} won the raffle"


def _fmt_stream_state(event: StreamStateEvent) -> str:
    ts = _ts(event.timestamp)
    label = "ONLINE" if event.state == "online" else "OFFLINE"
    return f"[{ts}] === {label} ==="


def _fmt_hype_train(event: HypeTrainEvent) -> str:
    ts = _ts(event.timestamp)
    if event.kind == "begin":
        return f"[{ts}] === HYPE TRAIN BEGIN ==="
    return (
        f"[{ts}] === HYPE TRAIN END"
        f" (level={event.level}, total={event.total}) ==="
    )


def _fmt_song_request(event: SongRequestEvent) -> str:
    ts = _ts(event.timestamp)
    requester = event.requester or "unknown"
    return f'[{ts}] SONG REQUEST from {requester}: "{event.title}"'


_FORMATTERS: dict[type[OngwatchEvent], Callable[[Any], str]] = {
    CashSupportEvent:  _fmt_cash,
    SubscriptionEvent: _fmt_sub,
    GiftSubEvent:      _fmt_giftsub,
    RaidIncomingEvent: _fmt_raid_incoming,
    RaidOutgoingEvent: _fmt_raid_outgoing,
    RaffleWinEvent:    _fmt_raffle,
    StreamStateEvent:  _fmt_stream_state,
    HypeTrainEvent:    _fmt_hype_train,
    SongRequestEvent:  _fmt_song_request,
}


class ConsoleOutput:
    def __init__(
        self,
        stream: IO[str] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._stream = stream or sys.stdout
        self._log = logger or logging.getLogger("console")

    async def start(self) -> None:
        self._log.debug("console output started")

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
        formatter = _FORMATTERS.get(type(event))
        if formatter is None:
            self._log.debug("rejecting unhandled event type %s", type(event).__name__)
            return SendStatus.REJECTED
        self._write(formatter(event), event.is_test)
        return SendStatus.HANDLED


def create(config: dict[str, Any], logger: logging.Logger) -> ConsoleOutput:
    """Factory called by ongwatch.py when loading outputs from ongwatch.conf."""
    return ConsoleOutput(logger=logger)
