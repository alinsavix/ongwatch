from __future__ import annotations

import json
import logging
from collections.abc import Callable
from contextlib import suppress
from datetime import datetime, timezone
from typing import Any

import aiosqlite

from ..events import (CashSupportEvent, GiftSubEvent, HypeTrainEvent,
                      OngwatchEvent, RaffleWinEvent, RaidIncomingEvent,
                      RaidOutgoingEvent, SongRequestEvent, StreamStateEvent,
                      SubscriptionEvent)
from . import SendStatus

# ---------------------------------------------------------------------------
# Schema — one table per currently-emitted event type + _heartbeat
# ---------------------------------------------------------------------------

_SCHEMA: list[str] = [
    """CREATE TABLE IF NOT EXISTS cash_support (
        id           INTEGER PRIMARY KEY,
        timestamp    TEXT    NOT NULL,
        backend      TEXT    NOT NULL,
        is_test      INTEGER NOT NULL DEFAULT 0,
        username     TEXT    NOT NULL,
        amount_cents INTEGER NOT NULL,
        kind         TEXT    NOT NULL,
        comment      TEXT,
        raw          TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS subscription (
        id        INTEGER PRIMARY KEY,
        timestamp TEXT    NOT NULL,
        backend   TEXT    NOT NULL,
        is_test   INTEGER NOT NULL DEFAULT 0,
        username  TEXT    NOT NULL,
        tier      INTEGER NOT NULL,
        is_resub  INTEGER NOT NULL,
        months    INTEGER,
        message   TEXT,
        raw       TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS gift_sub (
        id         INTEGER PRIMARY KEY,
        timestamp  TEXT    NOT NULL,
        backend    TEXT    NOT NULL,
        is_test    INTEGER NOT NULL DEFAULT 0,
        gifter     TEXT,
        recipients TEXT    NOT NULL,
        tier       INTEGER NOT NULL,
        count      INTEGER NOT NULL,
        raw        TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS raid_incoming (
        id           INTEGER PRIMARY KEY,
        timestamp    TEXT    NOT NULL,
        backend      TEXT    NOT NULL,
        is_test      INTEGER NOT NULL DEFAULT 0,
        from_channel TEXT    NOT NULL,
        viewer_count INTEGER NOT NULL,
        raw          TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS raid_outgoing (
        id           INTEGER PRIMARY KEY,
        timestamp    TEXT    NOT NULL,
        backend      TEXT    NOT NULL,
        is_test      INTEGER NOT NULL DEFAULT 0,
        to_channel   TEXT    NOT NULL,
        viewer_count INTEGER NOT NULL,
        raw          TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS stream_state (
        id        INTEGER PRIMARY KEY,
        timestamp TEXT    NOT NULL,
        backend   TEXT    NOT NULL,
        is_test   INTEGER NOT NULL DEFAULT 0,
        state     TEXT    NOT NULL,
        raw       TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS hype_train (
        id        INTEGER PRIMARY KEY,
        timestamp TEXT    NOT NULL,
        backend   TEXT    NOT NULL,
        is_test   INTEGER NOT NULL DEFAULT 0,
        kind      TEXT    NOT NULL,
        level     INTEGER NOT NULL,
        total     INTEGER NOT NULL,
        raw       TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS song_request (
        id        INTEGER PRIMARY KEY,
        timestamp TEXT    NOT NULL,
        backend   TEXT    NOT NULL,
        is_test   INTEGER NOT NULL DEFAULT 0,
        title     TEXT    NOT NULL,
        requester TEXT,
        raw       TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS raffle_win (
        id        INTEGER PRIMARY KEY,
        timestamp TEXT    NOT NULL,
        backend   TEXT    NOT NULL,
        is_test   INTEGER NOT NULL DEFAULT 0,
        winner    TEXT    NOT NULL,
        raw       TEXT
    )""",
    # Single-row table; upserted on each heartbeat
    """CREATE TABLE IF NOT EXISTS _heartbeat (
        id INTEGER PRIMARY KEY DEFAULT 1,
        ts TEXT NOT NULL
    )""",
]

# Migrations for existing databases. Each statement runs on every startup
# with OperationalError suppressed, so each must be a no-op (i.e. fail
# cleanly) once it has been applied or when it doesn't apply at all.
_MIGRATIONS: list[str] = [
    "ALTER TABLE cash_support  ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE subscription   ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE gift_sub       ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE raid           ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE raid_incoming  ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE raid_outgoing  ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE stream_state   ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE hype_train     ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE song_request   ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE raffle_win     ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
    """INSERT OR IGNORE INTO raid_incoming
        (id, timestamp, backend, is_test, from_channel, viewer_count, raw)
        SELECT id, timestamp, backend, is_test, from_channel, viewer_count, raw
        FROM raid""",
    # Money model change: float dollars ("amount") -> integer cents
    # ("amount_cents"). Backfill from the old column, then drop it so the
    # NOT NULL constraint on it can't break future inserts.
    "ALTER TABLE cash_support ADD COLUMN amount_cents INTEGER",
    """UPDATE cash_support
        SET amount_cents = CAST(ROUND(amount * 100) AS INTEGER)
        WHERE amount_cents IS NULL""",
    "ALTER TABLE cash_support DROP COLUMN amount",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def validate_config(config: dict[str, Any]) -> None:
    unknown = sorted(set(config) - {"path"})
    if unknown:
        raise ValueError(f"unknown sqlite config key(s): {', '.join(unknown)}")
    if "path" in config:
        path = config["path"]
        if not isinstance(path, str):
            raise ValueError("sqlite config value 'path' must be a string")
        if not path:
            raise ValueError("sqlite config value 'path' cannot be empty")


def _ts(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _raw(value: Any) -> str | None:
    """Best-effort JSON serialization of a raw backend payload."""
    if value is None:
        return None
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return json.dumps({"_repr": repr(value)})


# ---------------------------------------------------------------------------
# Per-event-type INSERT builders. Each returns (sql, params) for one row; the
# shared timestamp and serialized raw payload are passed in. To support a new
# event type, add a builder and a row in _INSERTS; unhandled types are REJECTED.
# ---------------------------------------------------------------------------

_Insert = tuple[str, tuple[Any, ...]]


def _cash_insert(event: CashSupportEvent, ts: str, raw: str | None) -> _Insert:
    return (
        "INSERT INTO cash_support"
        " (timestamp, backend, is_test, username, amount_cents, kind, comment, raw)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (ts, event.backend, int(event.is_test), event.username, event.amount_cents,
         event.kind, event.comment, raw),
    )


def _sub_insert(event: SubscriptionEvent, ts: str, raw: str | None) -> _Insert:
    return (
        "INSERT INTO subscription"
        " (timestamp, backend, is_test, username, tier, is_resub, months, message, raw)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (ts, event.backend, int(event.is_test), event.username, event.tier,
         int(event.is_resub), event.months, event.message, raw),
    )


def _giftsub_insert(event: GiftSubEvent, ts: str, raw: str | None) -> _Insert:
    return (
        "INSERT INTO gift_sub"
        " (timestamp, backend, is_test, gifter, recipients, tier, count, raw)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (ts, event.backend, int(event.is_test), event.gifter,
         json.dumps(event.recipients), event.tier, event.count, raw),
    )


def _raid_incoming_insert(event: RaidIncomingEvent, ts: str, raw: str | None) -> _Insert:
    return (
        "INSERT INTO raid_incoming"
        " (timestamp, backend, is_test, from_channel, viewer_count, raw)"
        " VALUES (?,?,?,?,?,?)",
        (ts, event.backend, int(event.is_test), event.from_channel, event.viewer_count, raw),
    )


def _raid_outgoing_insert(event: RaidOutgoingEvent, ts: str, raw: str | None) -> _Insert:
    return (
        "INSERT INTO raid_outgoing"
        " (timestamp, backend, is_test, to_channel, viewer_count, raw)"
        " VALUES (?,?,?,?,?,?)",
        (ts, event.backend, int(event.is_test), event.to_channel, event.viewer_count, raw),
    )


def _stream_state_insert(event: StreamStateEvent, ts: str, raw: str | None) -> _Insert:
    return (
        "INSERT INTO stream_state (timestamp, backend, is_test, state, raw)"
        " VALUES (?,?,?,?,?)",
        (ts, event.backend, int(event.is_test), event.state, raw),
    )


def _hype_train_insert(event: HypeTrainEvent, ts: str, raw: str | None) -> _Insert:
    return (
        "INSERT INTO hype_train"
        " (timestamp, backend, is_test, kind, level, total, raw)"
        " VALUES (?,?,?,?,?,?,?)",
        (ts, event.backend, int(event.is_test), event.kind, event.level, event.total, raw),
    )


def _song_request_insert(event: SongRequestEvent, ts: str, raw: str | None) -> _Insert:
    return (
        "INSERT INTO song_request"
        " (timestamp, backend, is_test, title, requester, raw)"
        " VALUES (?,?,?,?,?,?)",
        (ts, event.backend, int(event.is_test), event.title, event.requester, raw),
    )


def _raffle_insert(event: RaffleWinEvent, ts: str, raw: str | None) -> _Insert:
    return (
        "INSERT INTO raffle_win (timestamp, backend, is_test, winner, raw)"
        " VALUES (?,?,?,?,?)",
        (ts, event.backend, int(event.is_test), event.winner, raw),
    )


_INSERTS: dict[type[OngwatchEvent], Callable[[Any, str, str | None], _Insert]] = {
    CashSupportEvent:  _cash_insert,
    SubscriptionEvent: _sub_insert,
    GiftSubEvent:      _giftsub_insert,
    RaidIncomingEvent: _raid_incoming_insert,
    RaidOutgoingEvent: _raid_outgoing_insert,
    StreamStateEvent:  _stream_state_insert,
    HypeTrainEvent:    _hype_train_insert,
    SongRequestEvent:  _song_request_insert,
    RaffleWinEvent:    _raffle_insert,
}


# ---------------------------------------------------------------------------
# SQLiteOutput
# ---------------------------------------------------------------------------

class SQLiteOutput:
    def __init__(self, path: str, logger: logging.Logger | None = None) -> None:
        self._path = path
        self._db: aiosqlite.Connection | None = None
        self._log = logger or logging.getLogger("sqlite")

    async def start(self) -> None:
        self._log.info("sqlite output using database %s", self._path)
        self._db = await aiosqlite.connect(self._path)
        await self._db.execute("PRAGMA journal_mode=WAL")
        for stmt in _SCHEMA:
            await self._db.execute(stmt)
        for stmt in _MIGRATIONS:
            with suppress(aiosqlite.OperationalError):
                await self._db.execute(stmt)
        await self._db.commit()

    async def stop(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    async def heartbeat(self) -> None:
        assert self._db is not None
        ts = datetime.now(tz=timezone.utc).isoformat()
        await self._db.execute(
            "INSERT OR REPLACE INTO _heartbeat (id, ts) VALUES (1, ?)", (ts,)
        )
        await self._db.commit()

    async def send(self, event: OngwatchEvent) -> SendStatus:
        assert self._db is not None
        self._log.debug("send: %s", type(event).__name__)

        builder = _INSERTS.get(type(event))
        if builder is None:
            self._log.debug("rejecting unhandled event type %s", type(event).__name__)
            return SendStatus.REJECTED

        sql, params = builder(event, _ts(event.timestamp), _raw(event.raw))
        await self._db.execute(sql, params)
        await self._db.commit()
        return SendStatus.HANDLED


def create(config: dict[str, Any], logger: logging.Logger) -> SQLiteOutput:
    """Factory called by ongwatch.py when loading outputs from ongwatch.conf."""
    return SQLiteOutput(path=config.get("path", ":memory:"), logger=logger)
