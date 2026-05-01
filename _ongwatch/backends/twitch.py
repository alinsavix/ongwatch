from __future__ import annotations

import argparse
import logging
import re
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

import aiohttp
import twitchio
from twitchio import eventsub
from twitchio.models.eventsub_ import (ChannelBitsUse, ChannelRaid,
                                       ChatMessage, ChatNotification,
                                       HypeTrainBegin, HypeTrainEnd,
                                       StreamOffline, StreamOnline)

from ..dispatcher import Dispatcher
from ..events import (CashSupportEvent, GiftSubEvent, HypeTrainEvent,
                      RaffleWinEvent, RaidIncomingEvent, RaidOutgoingEvent,
                      SongRequestEvent, StreamStateEvent, SubscriptionEvent)
from ..util import get_token

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
    chatter = payload.chatter.display_name

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
        from_channel=payload.from_broadcaster.display_name,
        viewer_count=payload.viewer_count,
    )


def _map_raid_outgoing(payload: ChannelRaid) -> RaidOutgoingEvent:
    return RaidOutgoingEvent(
        timestamp=datetime.now(tz=timezone.utc),
        backend="twitch",
        raw=payload,
        to_channel=payload.to_broadcaster.display_name,
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

def _conduit_id_path(token_file: Path) -> Path:
    hostname = socket.gethostname().split(".")[0]
    # Extract env suffix from e.g. "twitch_user_token.prod.json" → "prod"
    env = token_file.stem.split(".")[-1]
    return token_file.parent / f"twitch_conduit_id.{env}.{hostname}.txt"


def _load_conduit_id(path: Path) -> str | bool:
    if path.exists():
        return path.read_text().strip()
    return True  # True = ask AutoClient to create a new conduit


def _save_conduit_id(path: Path, conduit_id: str) -> None:
    path.write_text(conduit_id)


# ---------------------------------------------------------------------------
# Token pre-validation (needed to get user_id before constructing AutoClient)
# ---------------------------------------------------------------------------

async def _validate_token(access_token: str) -> str:
    async with (
        aiohttp.ClientSession() as session,
        session.get(
            "https://id.twitch.tv/oauth2/validate",
            headers={"Authorization": f"OAuth {access_token}"},
        ) as resp,
    ):
        resp.raise_for_status()
        return (await resp.json())["user_id"]


# ---------------------------------------------------------------------------
# TwitchIO client
# ---------------------------------------------------------------------------

class OngWatch_Twitch(twitchio.AutoClient):
    botargs: argparse.Namespace
    logger: logging.Logger
    dispatcher: Dispatcher
    request_urls: Dict[str, str]
    _subscriptions: list
    _conduit_id_path: Path

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        bot_id: str,
        botargs: argparse.Namespace,
        logger: logging.Logger,
        dispatcher: Dispatcher,
        subscriptions: list,
        conduit_id: str | bool,
        conduit_id_path: Path,
    ) -> None:
        self.botargs = botargs
        self.logger = logger
        self.dispatcher = dispatcher
        self.request_urls = {}
        self._subscriptions = subscriptions
        self._conduit_id_path = conduit_id_path
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            bot_id=bot_id,
            conduit_id=conduit_id,
        )

    async def setup_hook(self) -> None:
        result = await self.multi_subscribe(self._subscriptions, stop_on_error=True)
        self.logger.info(f"Subscribed to {len(result.success)} EventSub subscriptions")
        _save_conduit_id(self._conduit_id_path, self.conduit_info.id)

    async def event_ready(self) -> None:
        self.logger.info("Client is ready")

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
        chatter_name = payload.chatter.display_name

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

    tokens = get_token(args.token_file)
    user_id = await _validate_token(tokens['token'])

    subs = [
        eventsub.ChatMessageSubscription(
            broadcaster_user_id=user_id,
            user_id=user_id,
        ),
        eventsub.ChatNotificationSubscription(
            broadcaster_user_id=user_id,
            user_id=user_id,
        ),
        eventsub.ChannelBitsUseSubscription(
            broadcaster_user_id=user_id,
        ),
        eventsub.StreamOnlineSubscription(
            broadcaster_user_id=user_id,
        ),
        eventsub.StreamOfflineSubscription(
            broadcaster_user_id=user_id,
        ),
        eventsub.HypeTrainBeginSubscription(
            broadcaster_user_id=user_id,
        ),
        eventsub.HypeTrainEndSubscription(
            broadcaster_user_id=user_id,
        ),
        eventsub.ChannelRaidSubscription(
            to_broadcaster_user_id=user_id,
        ),
    ]

    token_file = Path(args.token_file)
    conduit_path = _conduit_id_path(token_file)
    conduit_id = _load_conduit_id(conduit_path)

    client = OngWatch_Twitch(
        client_id=creds['client_id'],
        client_secret=creds['client_secret'],
        bot_id=user_id,
        botargs=args,
        logger=logger,
        dispatcher=dispatcher,
        subscriptions=subs,
        conduit_id=conduit_id,
        conduit_id_path=conduit_path,
    )

    logger.info("Starting Twitch backend")

    async with client:
        await client.add_token(tokens['token'], tokens['refresh'])
        # no need to save our tokens, since we're using DCF tokens
        await client.start(load_tokens=False, save_tokens=False, with_adapter=False)
