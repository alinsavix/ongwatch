from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import aiosqlite

from ..events import (CashSupportEvent, GiftSubEvent, HypeTrainEvent,
                      OngwatchEvent, RaffleWinEvent, RaidEvent,
                      SongRequestEvent, StreamStateEvent, SubscriptionEvent)
from . import SendStatus

# ---------------------------------------------------------------------------
# Schema — one table per currently-emitted event type + _heartbeat
# ---------------------------------------------------------------------------

_SCHEMA: list[str] = [
    """CREATE TABLE IF NOT EXISTS cash_support (
        id        INTEGER PRIMARY KEY,
        timestamp TEXT    NOT NULL,
        backend   TEXT    NOT NULL,
        is_test   INTEGER NOT NULL DEFAULT 0,
        username  TEXT    NOT NULL,
        amount    REAL    NOT NULL,
        kind      TEXT    NOT NULL,
        comment   TEXT,
        raw       TEXT
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
    """CREATE TABLE IF NOT EXISTS raid (
        id           INTEGER PRIMARY KEY,
        timestamp    TEXT    NOT NULL,
        backend      TEXT    NOT NULL,
        is_test      INTEGER NOT NULL DEFAULT 0,
        from_channel TEXT    NOT NULL,
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

# Migrations for existing databases that predate the is_test column.
_MIGRATIONS: list[str] = [
    "ALTER TABLE cash_support  ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE subscription   ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE gift_sub       ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE raid           ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE stream_state   ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE hype_train     ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE song_request   ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE raffle_win     ADD COLUMN is_test INTEGER NOT NULL DEFAULT 0",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
# SQLiteOutput
# ---------------------------------------------------------------------------

class SQLiteOutput:
    def __init__(self, path: str) -> None:
        self._path = path
        self._db: aiosqlite.Connection | None = None

    async def start(self) -> None:
        self._db = await aiosqlite.connect(self._path)
        await self._db.execute("PRAGMA journal_mode=WAL")
        for stmt in _SCHEMA:
            await self._db.execute(stmt)
        for stmt in _MIGRATIONS:
            try:
                await self._db.execute(stmt)
            except aiosqlite.OperationalError:
                pass  # column already exists
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
        ts = _ts(event.timestamp)
        raw = _raw(event.raw)

        if isinstance(event, CashSupportEvent):
            await self._db.execute(
                "INSERT INTO cash_support"
                " (timestamp, backend, is_test, username, amount, kind, comment, raw)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (ts, event.backend, int(event.is_test), event.username, event.amount,
                 event.kind, event.comment, raw),
            )
            await self._db.commit()
            return SendStatus.HANDLED

        if isinstance(event, SubscriptionEvent):
            await self._db.execute(
                "INSERT INTO subscription"
                " (timestamp, backend, is_test, username, tier, is_resub, months, message, raw)"
                " VALUES (?,?,?,?,?,?,?,?,?)",
                (ts, event.backend, int(event.is_test), event.username, event.tier,
                 int(event.is_resub), event.months, event.message, raw),
            )
            await self._db.commit()
            return SendStatus.HANDLED

        if isinstance(event, GiftSubEvent):
            await self._db.execute(
                "INSERT INTO gift_sub"
                " (timestamp, backend, is_test, gifter, recipients, tier, count, raw)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (ts, event.backend, int(event.is_test), event.gifter,
                 json.dumps(event.recipients), event.tier, event.count, raw),
            )
            await self._db.commit()
            return SendStatus.HANDLED

        if isinstance(event, RaidEvent):
            await self._db.execute(
                "INSERT INTO raid"
                " (timestamp, backend, is_test, from_channel, viewer_count, raw)"
                " VALUES (?,?,?,?,?,?)",
                (ts, event.backend, int(event.is_test), event.from_channel, event.viewer_count, raw),
            )
            await self._db.commit()
            return SendStatus.HANDLED

        if isinstance(event, StreamStateEvent):
            await self._db.execute(
                "INSERT INTO stream_state (timestamp, backend, is_test, state, raw)"
                " VALUES (?,?,?,?,?)",
                (ts, event.backend, int(event.is_test), event.state, raw),
            )
            await self._db.commit()
            return SendStatus.HANDLED

        if isinstance(event, HypeTrainEvent):
            await self._db.execute(
                "INSERT INTO hype_train"
                " (timestamp, backend, is_test, kind, level, total, raw)"
                " VALUES (?,?,?,?,?,?,?)",
                (ts, event.backend, int(event.is_test), event.kind, event.level, event.total, raw),
            )
            await self._db.commit()
            return SendStatus.HANDLED

        if isinstance(event, SongRequestEvent):
            await self._db.execute(
                "INSERT INTO song_request"
                " (timestamp, backend, is_test, title, requester, raw)"
                " VALUES (?,?,?,?,?,?)",
                (ts, event.backend, int(event.is_test), event.title, event.requester, raw),
            )
            await self._db.commit()
            return SendStatus.HANDLED

        if isinstance(event, RaffleWinEvent):
            await self._db.execute(
                "INSERT INTO raffle_win (timestamp, backend, is_test, winner, raw)"
                " VALUES (?,?,?,?,?)",
                (ts, event.backend, int(event.is_test), event.winner, raw),
            )
            await self._db.commit()
            return SendStatus.HANDLED

        return SendStatus.REJECTED


def create(config: dict[str, Any]) -> SQLiteOutput:
    """Factory called by ongwatch.py when loading outputs from ongwatch.conf."""
    return SQLiteOutput(path=config.get("path", ":memory:"))
