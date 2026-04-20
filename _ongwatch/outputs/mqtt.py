from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import aiomqtt

from ..events import (CashSupportEvent, GiftSubEvent, HypeTrainEvent,
                      OngwatchEvent, RaffleWinEvent, RaidEvent,
                      SongRequestEvent, StreamStateEvent, SubscriptionEvent)
from . import SendStatus

# ---------------------------------------------------------------------------
# Topic layout (from TOPICS.md):
#   {channel}/support/direct    — cash/tips/bits     (no retain, qos_events)
#   {channel}/support/sub       — subscriptions      (no retain, qos_events)
#   {channel}/support/giftsub   — gift subs          (no retain, qos_events)
#   {channel}/raid/incoming     — incoming raid       (no retain, qos_events)
#   {channel}/stream/status     — stream state        (retained,  qos_state)
#   {channel}/hypetrain/status  — hype train          (retained,  qos_state)
#   {channel}/songqueue/request — song request        (no retain, qos_events)
#   {channel}/raffle/win        — raffle winner       (no retain, qos_events)
#   {channel}/heartbeat         — watchdog tick       (no retain, qos_heartbeat)
#   {channel}/presence          — LWT / online signal (retained,  QoS 1)
# ---------------------------------------------------------------------------

# (topic_suffix, event_type, retain, use_state_qos)
_EVENT_MAP: dict[type[OngwatchEvent], tuple[str, str, bool, bool]] = {
    CashSupportEvent:  ("support/direct",    "cash_support",  False, False),
    SubscriptionEvent: ("support/sub",        "subscription",  False, False),
    GiftSubEvent:      ("support/giftsub",    "gift_sub",      False, False),
    RaidEvent:         ("raid/incoming",      "raid_incoming", False, False),
    StreamStateEvent:  ("stream/status",      "stream_status", True,  True),
    HypeTrainEvent:    ("hypetrain/status",   "hype_train",    True,  True),
    SongRequestEvent:  ("songqueue/request",  "song_request",  False, False),
    RaffleWinEvent:    ("raffle/win",         "raffle_win",    False, False),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
        return {"username": event.username, "amount": event.amount,
                "kind": event.kind, "comment": event.comment}
    if isinstance(event, SubscriptionEvent):
        return {"username": event.username, "tier": event.tier,
                "is_resub": event.is_resub, "months": event.months,
                "message": event.message}
    if isinstance(event, GiftSubEvent):
        return {"gifter": event.gifter, "recipients": event.recipients,
                "tier": event.tier, "count": event.count}
    if isinstance(event, RaidEvent):
        return {"from_channel": event.from_channel, "viewer_count": event.viewer_count}
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
    return json.dumps({
        "v": 1,
        "timestamp": _ts(event.timestamp),
        "backend": event.backend,
        "event_type": event_type,
        "data": data,
        "raw": _raw_json(event.raw),
    })


# ---------------------------------------------------------------------------
# MQTTOutput
# ---------------------------------------------------------------------------

class MQTTOutput:
    def __init__(self, config: dict[str, Any]) -> None:
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
        client = self._make_client()
        await client.__aenter__()
        self._client = client
        await client.publish(self._topic("presence"), "online", qos=1, retain=True)

    async def _disconnect(self, publish_offline: bool = True) -> None:
        client, self._client = self._client, None
        if client is None:
            return
        if publish_offline:
            try:
                await client.publish(
                    self._topic("presence"), "offline", qos=1, retain=True
                )
            except Exception:
                pass
        try:
            await client.__aexit__(None, None, None)
        except Exception:
            pass

    async def start(self) -> None:
        await self._connect()

    async def stop(self) -> None:
        await self._disconnect(publish_offline=True)

    async def heartbeat(self) -> None:
        if self._client is None:
            await self._connect()   # raises aiomqtt.MqttError on failure
        assert self._client is not None
        await self._client.publish(
            self._topic("heartbeat"), "", qos=self._qos_heartbeat, retain=False
        )

    async def send(self, event: OngwatchEvent) -> SendStatus:
        if self._client is None:
            return SendStatus.TRANSIENT

        entry = _EVENT_MAP.get(type(event))
        if entry is None:
            return SendStatus.REJECTED

        topic_suffix, event_type, retain, use_state_qos = entry
        qos = self._qos_state if use_state_qos else self._qos_events
        payload = _envelope(event, event_type, _build_data(event))

        try:
            await self._client.publish(
                self._topic(topic_suffix), payload, qos=qos, retain=retain
            )
            return SendStatus.HANDLED
        except aiomqtt.MqttError:
            await self._disconnect(publish_offline=False)
            return SendStatus.TRANSIENT


def create(config: dict[str, Any]) -> MQTTOutput:
    """Factory called by ongwatch.py when loading outputs from ongwatch.conf."""
    return MQTTOutput(config)
