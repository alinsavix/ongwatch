import argparse
import json
import logging
import re
import socket
from pathlib import Path
from typing import Dict

from _ongwatch.util import now, out, printextra, printsupport

import twitchio
from twitchio import eventsub
from twitchio.models.eventsub_ import (ChannelBitsUse, ChannelRaid,
                                       ChatMessage, ChatNotification,
                                       HypeTrainBegin, HypeTrainEnd,
                                       StreamOffline, StreamOnline)

# Best I can tell, this info is simply not available from the API,
# so we have to hardcode it. Units are in bits. Not currently used,
# but keeping around in case it's useful.
AUTOMATIC_REWARD_COSTS = {
    "message_effect": 10,
    "gigantify_an_emote": 30,
    "celebration": 60
}

# units are in dollars
SUB_VALUES = {
    1000: 5.00,
    2000: 10.00,
    3000: 25.00,
}


# ---------------------------------------------------------------------------
# Conduit ID + tokens-file path helpers
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
    with open(tokens_path) as f:
        data = json.load(f)
    return next(iter(data))


class OngWatch_Twitch(twitchio.AutoClient):
    botargs: argparse.Namespace
    logger: logging.Logger
    request_urls: Dict[str, str]
    _subscriptions: list
    _conduit_id_path: Path
    _tokens_path: Path

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        bot_id: str,
        botargs: argparse.Namespace,
        logger: logging.Logger,
        subscriptions: list,
        conduit_id: str | bool,
        conduit_id_path: Path,
        tokens_path: Path,
    ) -> None:
        self.botargs = botargs
        self.logger = logger
        self.request_urls = {}
        self._subscriptions = subscriptions
        self._conduit_id_path = conduit_id_path
        self._tokens_path = tokens_path
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            bot_id=bot_id,
            conduit_id=conduit_id,
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
        _save_conduit_id(self._conduit_id_path, self.conduit_info.id)

    async def event_ready(self) -> None:
        self.logger.info("Client is ready")

    async def event_stream_online(self, payload: StreamOnline) -> None:
        self.logger.debug(f"Stream online received")
        out(f"=== ONLINE (type={payload.type} @ {payload.started_at}) ===")

    async def event_stream_offline(self, payload: StreamOffline) -> None:
        self.logger.debug(f"Stream offline received")
        out("=== OFFLINE ===")

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

    def _handle_nightbot_text(self, chatmsg: str) -> None:
        if (m := self.rafflewin_re.match(chatmsg)):
            user = m.group("user")
            self.logger.info(f"Nightbot announces raffle winner: {user}")
            printsupport(ts=now(), supporter=user, support_type="Raffle", amount=0.0)
            return

        if (m := self.request_re.match(chatmsg)):
            user = m.group("user")
            title = m.group("title")
            req_url = self.request_urls.pop(user, "")
            linkstr = f'=HYPERLINK("{req_url}", "{title}")'
            printextra(ts=now(), message=f"SONG REQUEST FROM {user}: {linkstr}")
            return

        self.logger.debug(f"Nightbot message, not interesting: {chatmsg}")

    # FIXME: split chat message handling somehow, not sure what makes sense
    async def event_message(self, payload: ChatMessage) -> None:
        self.logger.debug(f"Chat message received")
        chatter_name = payload.chatter.display_name

        if chatter_name == "Nightbot":
            self._handle_nightbot_text(payload.text)
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
    # we do actualy get separate events for subs/resubs/gift
    # subs/etc, but they don't have all the info we need.
    #
    # Sigh.
    async def event_chat_notification(self, payload: ChatNotification) -> None:
        self.logger.debug(f"Chat notification received")
        chatter_name = payload.chatter.display_name

        if chatter_name == "Nightbot":
            self._handle_nightbot_text(payload.text)
            return

        if payload.anonymous:
            chatter = "AnAnonymousGifter"
        else:
            chatter = chatter_name

        if payload.sub_gift is not None:
            gifter = chatter
            recipient = payload.sub_gift.recipient.display_name
            tier = int(payload.sub_gift.tier)   # "1000" -> 1000
            months = 0
        elif payload.sub is not None:
            gifter = ""
            recipient = chatter
            tier = int(payload.sub.tier)
            months = 1
        elif payload.resub is not None:
            gifter = ""
            recipient = chatter
            tier = int(payload.resub.tier)
            months = payload.resub.cumulative_months or 0
        else:
            return

        if months == 0:
            sub_str = "Sub"
        else:
            sub_str = f"Sub #{months}"

        value = SUB_VALUES[tier]
        self.logger.info(f"output sub: {value} for {recipient}")
        printsupport(ts=now(), gifter=gifter, supporter=recipient, support_type=sub_str, amount=value)

    async def event_bits_use(self, payload: ChannelBitsUse) -> None:
        self.logger.debug(f"Bits use received: {payload.bits}")
        user_name = payload.user.display_name if payload.user else "Unknown"
        self.logger.info(f"output bit use: {payload.bits} for {user_name}")
        printsupport(ts=now(), supporter=user_name, support_type="Bits", amount=payload.bits / 100.0)

    async def event_hype_train(self, payload: HypeTrainBegin) -> None:
        self.logger.debug(f"Hype train begin received")
        out("=== HYPE TRAIN BEGIN ===")

    async def event_hype_train_end(self, payload: HypeTrainEnd) -> None:
        self.logger.debug(f"Hype train end received")
        out(f"=== HYPE TRAIN END (level={payload.level}, total={payload.total}) ===")

    async def event_raid(self, payload: ChannelRaid) -> None:
        self.logger.debug(f"Raid received")
        if payload.from_broadcaster.id == self.bot_id:
            return

        from_user = payload.from_broadcaster.display_name
        viewers = payload.viewer_count
        self.logger.info(f"output raid: {viewers} from {from_user}")
        printsupport(ts=now(), supporter=from_user, support_type=f"Raid - {viewers}", amount=0.0)


async def start(args: argparse.Namespace, creds: Dict[str, str] | None, logger: logging.Logger) -> None:
    if creds is None:
        raise ValueError("No credentials specified")

    env: str = args.environment
    tokens_path = _tio_tokens_path(env)
    conduit_path = _conduit_id_path(env)
    conduit_id = _load_conduit_id(conduit_path)
    bot_id = _read_bot_id(tokens_path)

    subs = [
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
        subscriptions=subs,
        conduit_id=conduit_id,
        conduit_id_path=conduit_path,
        tokens_path=tokens_path,
    )

    logger.info(f"Starting Twitch backend")

    async with client:
        await client.start(with_adapter=False)
