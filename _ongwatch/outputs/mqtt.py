from __future__ import annotations

import json
import logging
from contextlib import suppress
from datetime import datetime, timezone
from typing import Any

import aiomqtt
from aiomqtt.exceptions import MqttCodeError

from ..events import (CashSupportEvent, GiftSubEvent, HypeTrainEvent,
                      OngwatchEvent, RaffleWinEvent, RaidIncomingEvent,
                      RaidOutgoingEvent, SongRequestEvent, StreamStateEvent,
                      SubscriptionEvent)
from . import SendStatus

# ---------------------------------------------------------------------------
# Topic layout (from TOPICS.md):
#   {channel}/support/direct    — cash/tips/bits     (no retain, qos_events)
#   {channel}/support/sub       — subscriptions      (no retain, qos_events)
#   {channel}/support/giftsub   — gift subs          (no retain, qos_events)
#   {channel}/raid/incoming     — incoming raid       (no retain, qos_events)
#   {channel}/raid/outgoing     — outgoing raid       (no retain, qos_events)
#   {channel}/stream/status     — stream state        (retained,  qos_state)
#   {channel}/hypetrain/status  — hype train          (retained,  qos_state)
#   {channel}/songqueue/request — song request        (no retain, qos_events)
#   {channel}/raffle/win        — raffle winner       (no retain, qos_events)
#   {channel}/heartbeat         — watchdog tick       (no retain, qos_heartbeat)
#   {channel}/presence          — LWT / online signal (retained,  QoS 1)
# ---------------------------------------------------------------------------

# (topic_suffix, event_type, retain, use_state_qos)
_EVENT_MAP: dict[type[OngwatchEvent], tuple[str, str, bool, bool]] = {
    CashSupportEvent:  ("support/direct",    "CashSupport",   False, False),
    SubscriptionEvent: ("support/sub",        "Subscription",  False, False),
    GiftSubEvent:      ("support/giftsub",    "GiftSub",       False, False),
    RaidIncomingEvent: ("raid/incoming",      "RaidIncoming",  False, False),
    RaidOutgoingEvent: ("raid/outgoing",      "RaidOutgoing",  False, False),
    StreamStateEvent:  ("stream/status",      "StreamStatus",  True,  True),
    HypeTrainEvent:    ("hypetrain/status",   "HypeTrain",     True,  True),
    SongRequestEvent:  ("songqueue/request",  "SongRequest",   False, False),
    RaffleWinEvent:    ("raffle/win",         "RaffleWin",     False, False),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONFIG_KEYS = {
    "host",
    "port",
    "channel",
    "topic_prefix",
    "client_id",
    "username",
    "password",
    "tls",
    "qos_events",
    "qos_state",
    "qos_heartbeat",
}

_PERMANENT_CONNECT_CODES = {1, 2, 4, 5}
_PERMANENT_CONNECT_MESSAGES = (
    "bad username",
    "bad user name",
    "bad password",
    "not authorised",
    "not authorized",
    "invalid client identifier",
    "client identifier not valid",
    "incorrect protocol version",
    "unsupported protocol version",
)


class PermanentMQTTError(RuntimeError):
    """MQTT configuration/authorization failure that retries cannot fix."""


def _validate_unknown_keys(config: dict[str, Any]) -> None:
    unknown = sorted(set(config) - _CONFIG_KEYS)
    if unknown:
        raise ValueError(f"unknown MQTT config key(s): {', '.join(unknown)}")


def _validate_str(
    config: dict[str, Any],
    key: str,
    *,
    required: bool = False,
    allow_empty: bool = True,
) -> None:
    if key not in config:
        if required:
            raise ValueError(f"MQTT config requires '{key}'")
        return
    value = config[key]
    if not isinstance(value, str):
        raise ValueError(f"MQTT config value '{key}' must be a string")
    if not allow_empty and not value:
        raise ValueError(f"MQTT config value '{key}' cannot be empty")


def _validate_int(
    config: dict[str, Any],
    key: str,
    default: int,
    *,
    min_value: int,
    max_value: int,
) -> None:
    value = config.get(key, default)
    if isinstance(value, bool):
        raise ValueError(f"MQTT config value '{key}' must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"MQTT config value '{key}' must be an integer") from exc
    if parsed < min_value or parsed > max_value:
        raise ValueError(
            f"MQTT config value '{key}' must be between {min_value} and {max_value}"
        )


def validate_config(config: dict[str, Any]) -> None:
    """Validate MQTT-owned config keys."""
    _validate_unknown_keys(config)
    _validate_str(config, "channel", required=True, allow_empty=False)
    for key in ("host", "topic_prefix", "client_id", "username", "password"):
        _validate_str(config, key)
    _validate_int(config, "port", 1883, min_value=1, max_value=65535)
    _validate_int(config, "qos_events", 1, min_value=0, max_value=2)
    _validate_int(config, "qos_state", 1, min_value=0, max_value=2)
    _validate_int(config, "qos_heartbeat", 0, min_value=0, max_value=2)
    if "tls" in config and not isinstance(config["tls"], bool):
        raise ValueError("MQTT config value 'tls' must be a boolean")


def _is_permanent_connect_error(exc: aiomqtt.MqttError) -> bool:
    if isinstance(exc, MqttCodeError):
        rc = exc.rc
        if isinstance(rc, int):
            return rc in _PERMANENT_CONNECT_CODES
        reason = str(rc).lower()
        return any(message in reason for message in _PERMANENT_CONNECT_MESSAGES)

    message = str(exc).lower()
    return any(fragment in message for fragment in _PERMANENT_CONNECT_MESSAGES)


def _ts(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _raw_json(value: Any) -> Any:
    """Best-effort JSON-serializable form of a raw backend payload."""
    if value is None:
        return None
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return {"_repr": repr(value)}


def _build_data(event: OngwatchEvent) -> dict[str, Any]:
    if isinstance(event, CashSupportEvent):
        return {"username": event.username, "amount_cents": event.amount_cents,
                "kind": event.kind, "comment": event.comment}
    if isinstance(event, SubscriptionEvent):
        return {"username": event.username, "tier": event.tier,
                "is_resub": event.is_resub, "months": event.months,
                "message": event.message}
    if isinstance(event, GiftSubEvent):
        return {"gifter": event.gifter, "recipients": event.recipients,
                "tier": event.tier, "count": event.count}
    if isinstance(event, RaidIncomingEvent):
        return {"from_channel": event.from_channel, "viewer_count": event.viewer_count}
    if isinstance(event, RaidOutgoingEvent):
        return {"to_channel": event.to_channel, "viewer_count": event.viewer_count}
    if isinstance(event, StreamStateEvent):
        return {"state": event.state}
    if isinstance(event, HypeTrainEvent):
        return {"kind": event.kind, "level": event.level, "total": event.total}
    if isinstance(event, SongRequestEvent):
        return {"title": event.title, "requester": event.requester}
    if isinstance(event, RaffleWinEvent):
        return {"winner": event.winner}
    return {}


def _envelope(event: OngwatchEvent, event_type: str, data: dict[str, Any]) -> str:
    # v2: CashSupport "amount" (float dollars) became "amount_cents" (int)
    return json.dumps({
        "v": 2,
        "timestamp": _ts(event.timestamp),
        "backend": event.backend,
        "is_test": event.is_test,
        "event_type": event_type,
        "data": data,
        "raw": _raw_json(event.raw),
    })


# ---------------------------------------------------------------------------
# MQTTOutput
# ---------------------------------------------------------------------------

class MQTTOutput:
    def __init__(self, config: dict[str, Any], logger: logging.Logger | None = None) -> None:
        self._log = logger or logging.getLogger("mqtt")
        self._host: str = config.get("host", "localhost")
        self._port: int = int(config.get("port", 1883))
        self._channel: str = config["channel"]
        self._topic_prefix: str = config.get("topic_prefix", "")
        self._client_id: str = config.get("client_id", "") or f"ongwatch-{self._channel}"
        self._username: str | None = config.get("username") or None
        self._password: str | None = config.get("password") or None
        self._qos_events: int = int(config.get("qos_events", 1))
        self._qos_state: int = int(config.get("qos_state", 1))
        self._qos_heartbeat: int = int(config.get("qos_heartbeat", 0))
        self._client: aiomqtt.Client | None = None
        self._permanent_error: PermanentMQTTError | None = None

    def _topic(self, suffix: str) -> str:
        if self._topic_prefix:
            return f"{self._topic_prefix}/{self._channel}/{suffix}"
        return f"{self._channel}/{suffix}"

    def _make_client(self) -> aiomqtt.Client:
        will = aiomqtt.Will(
            topic=self._topic("presence"),
            payload="offline",
            qos=1,
            retain=True,
        )
        return aiomqtt.Client(
            self._host,
            self._port,
            identifier=self._client_id,
            username=self._username,
            password=self._password,
            will=will,
        )

    async def _connect(self) -> None:
        if self._permanent_error is not None:
            raise self._permanent_error

        client = self._make_client()
        try:
            await client.__aenter__()
        except aiomqtt.MqttError as exc:
            # Ensure paho's network thread is stopped even on connection failure.
            with suppress(Exception):
                await client.__aexit__(None, None, None)
            if _is_permanent_connect_error(exc):
                self._permanent_error = PermanentMQTTError(
                    f"MQTT permanent connection failure for "
                    f"{self._host}:{self._port}: {exc}"
                )
                raise self._permanent_error from exc
            raise
        self._client = client
        self._log.debug("connected to %s:%d as %s", self._host, self._port, self._client_id)
        await client.publish(self._topic("presence"), "online", qos=1, retain=True)

    async def _disconnect(self, publish_offline: bool = True) -> None:
        client, self._client = self._client, None
        if client is None:
            return
        if publish_offline:
            with suppress(Exception):
                await client.publish(
                    self._topic("presence"), "offline", qos=1, retain=True
                )
        with suppress(Exception):
            await client.__aexit__(None, None, None)

    async def start(self) -> None:
        try:
            await self._connect()
        except PermanentMQTTError:
            self._log.error("MQTT: permanent connection failure", exc_info=True)
            raise
        except aiomqtt.MqttError as exc:
            self._log.warning("MQTT: could not connect to %s:%d — %s (will retry on heartbeat)",
                              self._host, self._port, exc)

    async def stop(self) -> None:
        await self._disconnect(publish_offline=True)

    async def heartbeat(self) -> None:
        if self._permanent_error is not None:
            raise self._permanent_error
        if self._client is None:
            await self._connect()   # raises aiomqtt.MqttError on failure
        assert self._client is not None
        try:
            await self._client.publish(
                self._topic("heartbeat"), "", qos=self._qos_heartbeat, retain=False
            )
        except aiomqtt.MqttError:
            # The connection is dead (e.g. the host slept and the socket was
            # silently dropped). Discard the stale client so the next heartbeat
            # reconnects via _connect(); otherwise we keep publishing into a
            # broken connection forever and never recover.
            await self._disconnect(publish_offline=False)
            raise

    async def send(self, event: OngwatchEvent) -> SendStatus:
        if self._permanent_error is not None:
            return SendStatus.ERROR

        if self._client is None:
            self._log.debug("not connected, deferring %s event", type(event).__name__)
            return SendStatus.TRANSIENT

        entry = _EVENT_MAP.get(type(event))
        if entry is None:
            self._log.debug("rejecting unhandled event type %s", type(event).__name__)
            return SendStatus.REJECTED

        topic_suffix, event_type, retain, use_state_qos = entry
        qos = self._qos_state if use_state_qos else self._qos_events
        payload = _envelope(event, event_type, _build_data(event))

        try:
            await self._client.publish(
                self._topic(topic_suffix), payload, qos=qos, retain=retain
            )
            self._log.debug("published %s to %s", event_type, self._topic(topic_suffix))
            return SendStatus.HANDLED
        except aiomqtt.MqttError as exc:
            self._log.debug("publish to %s failed: %s", self._topic(topic_suffix), exc)
            await self._disconnect(publish_offline=False)
            return SendStatus.TRANSIENT


def create(config: dict[str, Any], logger: logging.Logger) -> MQTTOutput:
    """Factory called by ongwatch.py when loading outputs from ongwatch.conf."""
    return MQTTOutput(config, logger=logger)
