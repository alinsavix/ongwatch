from __future__ import annotations

import argparse
import json
import logging
import re
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, cast

import twitchio
from twitchio import eventsub
from twitchio.eventsub.subscriptions import SubscriptionPayload
from twitchio.models.eventsub_ import (ChannelBitsUse, ChannelRaid,
                                       ChatMessage, ChatNotification,
                                       HypeTrainBegin, HypeTrainEnd,
                                       StreamOffline, StreamOnline)

from ..dispatcher import Dispatcher
from ..events import (CashSupportEvent, GiftSubEvent, HypeTrainEvent,
                      RaffleWinEvent, RaidIncomingEvent, RaidOutgoingEvent,
                      SongRequestEvent, StreamStateEvent, SubscriptionEvent)

# Best I can tell, this info is simply not available from the API,
# so we have to hardcode it. Units are in bits. Not currently used,
# but keeping around in case it's useful.
AUTOMATIC_REWARD_COSTS = {
    "message_effect": 10,
    "gigantify_an_emote": 30,
    "celebration": 60
}


# ---------------------------------------------------------------------------
# Pure mapping functions (raw TwitchIO payload → normalized OngwatchEvent)
# ---------------------------------------------------------------------------

def _map_bits_event(payload: ChannelBitsUse) -> CashSupportEvent:
    if payload.user and payload.user.display_name:
        username = payload.user.display_name
    else:
        username = "Unknown"

    return CashSupportEvent(
        timestamp=datetime.now(tz=timezone.utc),
        backend="twitch",
        raw=payload,
        username=username,
        amount=payload.bits / 100.0,
        kind="bits",
    )


def _map_chat_notification(
    payload: ChatNotification,
) -> SubscriptionEvent | GiftSubEvent | None:
    chatter = payload.chatter.display_name or "Unknown"

    ts = datetime.now(tz=timezone.utc)

    # FIXME: recipients is an array, but we only ever put one recipient in it?
    if payload.sub_gift is not None:
        if payload.sub_gift.recipient and payload.sub_gift.recipient.display_name:
            recipient = payload.sub_gift.recipient.display_name
        else:
            recipient = "Unknown"
        tier = int(payload.sub_gift.tier) // 1000
        # FIXME: Reconsider how we handle anonymous gifters
        return GiftSubEvent(
            timestamp=ts,
            backend="twitch",
            raw=payload,
            gifter="AnAnonymousGifter" if payload.anonymous else chatter,
            is_anonymous=payload.anonymous,
            recipients=[recipient],
            tier=tier,
            count=1,
        )

    if payload.sub is not None:
        tier = int(payload.sub.tier) // 1000
        return SubscriptionEvent(
            timestamp=ts,
            backend="twitch",
            raw=payload,
            username=chatter,
            tier=tier,
            is_resub=False,
            months=1,
        )

    if payload.resub is not None:
        tier = int(payload.resub.tier) // 1000
        months = payload.resub.cumulative_months or None
        return SubscriptionEvent(
            timestamp=ts,
            backend="twitch",
            raw=payload,
            username=chatter,
            tier=tier,
            is_resub=True,
            months=months,
        )

    return None


def _map_raid_incoming(payload: ChannelRaid) -> RaidIncomingEvent:
    return RaidIncomingEvent(
        timestamp=datetime.now(tz=timezone.utc),
        backend="twitch",
        raw=payload,
        from_channel=payload.from_broadcaster.display_name or "Unknown",
        viewer_count=payload.viewer_count,
    )


def _map_raid_outgoing(payload: ChannelRaid) -> RaidOutgoingEvent:
    return RaidOutgoingEvent(
        timestamp=datetime.now(tz=timezone.utc),
        backend="twitch",
        raw=payload,
        to_channel=payload.to_broadcaster.display_name or "Unknown",
        viewer_count=payload.viewer_count,
    )


def _map_stream_online(payload: StreamOnline) -> StreamStateEvent:
    return StreamStateEvent(
        timestamp=datetime.now(tz=timezone.utc),
        backend="twitch",
        raw=payload,
        state="online",
    )


def _map_stream_offline(payload: StreamOffline) -> StreamStateEvent:
    return StreamStateEvent(
        timestamp=datetime.now(tz=timezone.utc),
        backend="twitch",
        raw=payload,
        state="offline",
    )


def _map_hype_train_begin(payload: HypeTrainBegin) -> HypeTrainEvent:
    return HypeTrainEvent(
        timestamp=datetime.now(tz=timezone.utc),
        backend="twitch",
        raw=payload,
        kind="begin",
        level=payload.level,
        total=payload.total,
    )


def _map_hype_train_end(payload: HypeTrainEnd) -> HypeTrainEvent:
    return HypeTrainEvent(
        timestamp=datetime.now(tz=timezone.utc),
        backend="twitch",
        raw=payload,
        kind="end",
        level=payload.level,
        total=payload.total,
    )


def _map_raffle_win(user: str, raw_payload: ChatMessage) -> RaffleWinEvent:
    return RaffleWinEvent(
        timestamp=datetime.now(tz=timezone.utc),
        backend="twitch",
        raw=raw_payload,
        winner=user,
    )


def _map_song_request(
    user: str, title: str, req_url: str, raw_payload: ChatMessage
) -> SongRequestEvent:
    return SongRequestEvent(
        timestamp=datetime.now(tz=timezone.utc),
        backend="twitch",
        raw={"payload": raw_payload, "req_url": req_url},
        title=title,
        requester=user,
    )


# ---------------------------------------------------------------------------
# Conduit ID persistence helpers
# ---------------------------------------------------------------------------

def _conduit_id_path(env: str) -> Path:
    hostname = socket.gethostname().split(".")[0]
    return Path.cwd() / f"twitch_conduit_id.{env}.{hostname}.txt"


def _load_conduit_id(path: Path) -> str | bool:
    if path.exists():
        return path.read_text().strip()
    return True  # True = ask AutoClient to create a new conduit


def _save_conduit_id(path: Path, conduit_id: str) -> None:
    path.write_text(conduit_id)


def _tio_tokens_path(env: str) -> Path:
    return Path.cwd() / f".tio.tokens.{env}.json"


def _read_bot_id(tokens_path: Path) -> str:
    # TwitchIO stores tokens as a dict keyed by user_id. Our use case has
    # exactly one user (the streamer), so the sole key is the bot_id.
    with tokens_path.open() as f:
        data = json.load(f)
    return cast(str, next(iter(data)))


# ---------------------------------------------------------------------------
# TwitchIO client
# ---------------------------------------------------------------------------

class OngWatch_Twitch(twitchio.AutoClient):
    botargs: argparse.Namespace
    logger: logging.Logger
    dispatcher: Dispatcher
    request_urls: Dict[str, str]
    _subscriptions: list[SubscriptionPayload]
    _conduit_id_path: Path
    _tokens_path: Path

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        bot_id: str,
        botargs: argparse.Namespace,
        logger: logging.Logger,
        dispatcher: Dispatcher,
        subscriptions: list[SubscriptionPayload],
        conduit_id: str | bool,
        conduit_id_path: Path,
        tokens_path: Path,
    ) -> None:
        self.botargs = botargs
        self.logger = logger
        self.dispatcher = dispatcher
        self.request_urls = {}
        self._subscriptions = subscriptions
        self._conduit_id_path = conduit_id_path
        self._tokens_path = tokens_path
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            bot_id=bot_id,
            conduit_id=cast(Any, conduit_id),
        )

    async def load_tokens(self, path: str | None = None, /) -> None:
        await super().load_tokens(path or str(self._tokens_path))

    async def save_tokens(self, path: str | None = None, /) -> None:
        await super().save_tokens(path or str(self._tokens_path))

    async def setup_hook(self) -> None:
        # Conduits persist subscriptions server-side, so on a reused conduit
        # most/all of these will come back as 409 Conflict ("already exists").
        # Ignore those; surface anything else as a warning.
        result = await self.multi_subscribe(self._subscriptions, stop_on_error=False)
        real_errors = [e for e in result.errors if e.error.status != 409]
        already_subscribed = len(result.errors) - len(real_errors)
        self.logger.info(
            f"EventSub: {len(result.success)} new, "
            f"{already_subscribed} already subscribed, "
            f"{len(real_errors)} failed"
        )
        for e in real_errors:
            self.logger.warning(f"Subscription failed: {e.subscription!r}: {e.error}")
        conduit_id = self.conduit_info.id
        if conduit_id is None:
            self.logger.warning("EventSub conduit has no ID to persist")
        else:
            _save_conduit_id(self._conduit_id_path, conduit_id)

    async def event_ready(self) -> None:
        self.logger.info("Twitch backend online and ready")

    async def event_stream_online(self, payload: StreamOnline) -> None:
        self.logger.debug("Stream online received")
        self.logger.info(f"Stream online (type={payload.type} @ {payload.started_at})")
        self.dispatcher.emit(_map_stream_online(payload))

    async def event_stream_offline(self, payload: StreamOffline) -> None:
        self.logger.debug("Stream offline received")
        self.logger.info("Stream offline")
        self.dispatcher.emit(_map_stream_offline(payload))

    request_re = re.compile(r"""
        ^@
        (?P<user>\S+)
        \s* -> \s*
        "
        (?P<title>.*)
        " \s+ by \s+
        (?P<ytname>.*)
        \s+
        has.been.added.to.the.queue
    """, re.VERBOSE)

    rafflewin_re = re.compile(r"""
        ^
        Congratulations,
        \s+
        (?P<user>\S+)!
        \s+
        You.won.the.giveaway
    """, re.VERBOSE)

    def _handle_nightbot_text(self, payload: ChatMessage) -> None:
        chatmsg = payload.text

        if (m := self.rafflewin_re.match(chatmsg)):
            user = m.group("user")
            self.logger.info(f"Nightbot announces raffle winner: {user}")
            self.dispatcher.emit(_map_raffle_win(user, payload))
            return

        if (m := self.request_re.match(chatmsg)):
            user = m.group("user")
            title = m.group("title")
            req_url = self.request_urls.pop(user, "")
            self.dispatcher.emit(_map_song_request(user, title, req_url, payload))
            return

        self.logger.debug(f"Nightbot message, not interesting: {chatmsg}")

    # FIXME: split chat message handling somehow, not sure what makes sense
    async def event_message(self, payload: ChatMessage) -> None:
        self.logger.debug("Chat message received")
        chatter_name = payload.chatter.display_name or "Unknown"

        if chatter_name == "Nightbot":
            self._handle_nightbot_text(payload)
            return

        if payload.text.lower().startswith("!sr "):
            user = chatter_name
            req_url = payload.text.split(" ")[1]
            self.request_urls[user] = req_url
            self.logger.debug(f"Saved song request from {user}: {req_url}")

    # This is kinda a train wreck -- the only way to get all the
    # info we need for logging subs/gift subs/resubs/etc, is to
    # look at the chat notification message (this one) and extract
    # what we want from that. This is weird and irritating, since
    # we do actually get separate events for subs/resubs/gift
    # subs/etc, but they don't have all the info we need.
    #
    # Sigh.
    async def event_chat_notification(self, payload: ChatNotification) -> None:
        self.logger.debug("Chat notification received")

        chatter_name = payload.chatter.display_name
        if chatter_name == "Nightbot":
            # Nightbot speaks via chat notifications too; handle the same way
            # (re-wrap as a minimal ChatMessage-like object is not worth it;
            # nightbot subscription announcements are ignored here)
            return

        event = _map_chat_notification(payload)
        if event is not None:
            self.logger.info(f"Sub/gift event: {type(event).__name__} for {chatter_name}")
            self.dispatcher.emit(event)

    async def event_bits_use(self, payload: ChannelBitsUse) -> None:
        self.logger.debug(f"Bits use received: {payload.bits}")
        user_name = payload.user.display_name if payload.user else "Unknown"
        self.logger.info(f"Bits: {payload.bits} from {user_name}")
        self.dispatcher.emit(_map_bits_event(payload))

    async def event_hype_train(self, payload: HypeTrainBegin) -> None:
        self.logger.debug("Hype train begin received")
        self.dispatcher.emit(_map_hype_train_begin(payload))

    async def event_hype_train_end(self, payload: HypeTrainEnd) -> None:
        self.logger.debug("Hype train end received")
        self.logger.info(f"Hype train end: level={payload.level}, total={payload.total}")
        self.dispatcher.emit(_map_hype_train_end(payload))

    async def event_raid(self, payload: ChannelRaid) -> None:
        self.logger.debug("Raid received")
        if payload.from_broadcaster.id == self.bot_id:
            self.logger.info(
                f"Raid out to {payload.to_broadcaster.display_name}"
                f" with {payload.viewer_count} viewers"
            )
            self.dispatcher.emit(_map_raid_outgoing(payload))
        else:
            self.logger.info(
                f"Raid from {payload.from_broadcaster.display_name}"
                f" with {payload.viewer_count} viewers"
            )
            self.dispatcher.emit(_map_raid_incoming(payload))


async def start(
    args: argparse.Namespace,
    creds: Dict[str, str] | None,
    logger: logging.Logger,
    dispatcher: Dispatcher,
) -> None:
    if creds is None:
        raise ValueError("No credentials specified")

    env: str = args.environment
    tokens_path = _tio_tokens_path(env)
    conduit_path = _conduit_id_path(env)
    conduit_id = _load_conduit_id(conduit_path)
    bot_id = _read_bot_id(tokens_path)

    subs: list[SubscriptionPayload] = [
        eventsub.ChatMessageSubscription(
            broadcaster_user_id=bot_id,
            user_id=bot_id,
        ),
        eventsub.ChatNotificationSubscription(
            broadcaster_user_id=bot_id,
            user_id=bot_id,
        ),
        eventsub.ChannelBitsUseSubscription(
            broadcaster_user_id=bot_id,
        ),
        eventsub.StreamOnlineSubscription(
            broadcaster_user_id=bot_id,
        ),
        eventsub.StreamOfflineSubscription(
            broadcaster_user_id=bot_id,
        ),
        eventsub.HypeTrainBeginSubscription(
            broadcaster_user_id=bot_id,
        ),
        eventsub.HypeTrainEndSubscription(
            broadcaster_user_id=bot_id,
        ),
        eventsub.ChannelRaidSubscription(
            to_broadcaster_user_id=bot_id,
        ),
    ]

    client = OngWatch_Twitch(
        client_id=creds['client_id'],
        client_secret=creds['client_secret'],
        bot_id=bot_id,
        botargs=args,
        logger=logger,
        dispatcher=dispatcher,
        subscriptions=subs,
        conduit_id=conduit_id,
        conduit_id_path=conduit_path,
        tokens_path=tokens_path,
    )

    logger.info("Starting Twitch backend")

    async with client:
        await client.start(with_adapter=False)
