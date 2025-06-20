# See https://twitchpy.readthedocs.io/ for docs

import argparse
import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, cast

from _ongwatch.outputs import dispatch_event
from _ongwatch.util import log, now, out, printextra, printsupport

from tdvutil import ppretty
from twitch import Client
from twitch.errors import HTTPException
from twitch.types import eventsub

# Best I can tell, this info is simply not available from the API,
# so we have to hardcode it. Units are in bits.
AUTOMATIC_REWARD_COSTS = {
    "message_effect": 10,
    "gigantify_an_emote": 30,
    "celebration": 60
}

# units are in dollars
# FIXME: the keys should actually be strings, per twitch docs
SUB_VALUES = {
    1000: 5.00,
    2000: 10.00,
    3000: 25.00,
}

def get_token(token_file: Path) -> Dict[str, str]:
    with open(token_file, 'r') as f:
        return cast(Dict[str, str], json.load(f))

class OngWatch_Twitch(Client):
    botargs: argparse.Namespace
    logger: logging.Logger
    request_urls: Dict[str, str] = {}

    def __init__(self, client_id: str, client_secret: str, **options: Any) -> None:
        if "botargs" in options:
            self.botargs = options["botargs"]

        if "logger" in options:
            self.logger = options["logger"]
        else:
            self.logger = logging.getLogger("twitch.client")

        super().__init__(client_id, client_secret, **options)


    # @staticmethod
    # async def on_error(event_name: str, error: Exception, /, *args: Any, **kwargs: Any) -> None:
    #     log(f"INFO: Error: {error}")

    # async def setup_hook(self) -> None:
    #     """Called when the client is setting up"""
    #     log("INFO: Setting up client")

    async def on_connect(self) -> None:
        self.logger.info('connection established')

    async def on_disconnect(self) -> None:
        self.logger.warning(f'disconnected')

    async def on_ready(self) -> None:
        """Called when the client is ready."""
        assert self.user is not None
        assert self.channel is not None

        self.logger.info("Client is ready")
        self.logger.info(f"User: {self.user.display_name} ({self.user.id})")
        self.logger.info(f"{self.total_subscription_cost} of {self.max_subscription_cost} subscription points used")
        self.logger.info(f"channel liveness: {await self.channel.stream.get_live()}")

        # total_subs = await self.channel.get_total_subscriptions()
        # total_pts = await self.channel.get_subscription_points()
        # log(f"Subscriptions: {total_subs} ({total_pts} pts)")

        # log("TW: Listening for events")

    # Only happens if socket_debug is true
    async def on_socket_raw_receive(self, data: Any) -> None:
        self.logger.debug(f"Socket raw receive: {data}")

    async def on_stream_online(self, data: eventsub.streams.StreamOnlineEvent) -> None:
        self.logger.info(f"Stream online received: {data}")
        out(f"=== ONLINE (type={data["type"]} @ {data["started_at"]} ===")
        await dispatch_event("stream.online", dict(data))

    async def on_stream_offline(self, data: eventsub.streams.StreamOfflineEvent) -> None:
        self.logger.info(f"Stream offline received: {data}")
        out("=== OFFLINE ===")
        await dispatch_event("stream.offline", dict(data))

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

    # FIXME: should we pass this already extracted fields?
    async def handle_nightbot(self, data: eventsub.chat.MessageEvent) -> None:
        self.logger.debug(f"Handling message as nightbot message")
        chatmsg = data.get("message", {}).get("text", "")

        if (m := self.rafflewin_re.match(chatmsg)):
            user = m.group("user")
            self.logger.info(f"Nightbot announces raffle winner: {user}")
            printsupport(ts=now(), supporter=user, type="Raffle", amount=0.0)
            return

        if (m := self.request_re.match(chatmsg)):
            user = m.group("user")
            # ytname = m.group("ytname")
            title = m.group("title")
            req_url = self.request_urls.get(user, "")

            linkstr = f'=HYPERLINK("{req_url}", "{title}")'
            printextra(ts=now(), message=f"SONG REQUEST FROM {user}: {linkstr}")
            del self.request_urls[user]
            return

        # else, wasn't interesting
        self.logger.debug(f"Got a message from nightbot, but not one we care about: {chatmsg}")
        return



    # FIXME: split chat message handling somehow, not sure what makes sense
    async def on_chat_message(self, data: eventsub.chat.MessageEvent) -> None:
        self.logger.debug(f"Chat notification received: {data}")

        chatmsg = data.get("message", {}).get("text", "")

        # For !sr handling, we need to track the requester when they make the
        # request, since the nightbot response doesn't actually include the URL.
        if chatmsg.startswith("!sr "):
            user = data.get("chatter_user_name", "UnknownUser")
            req_url = chatmsg.split(" ")[1]

            self.request_urls[user] = req_url
            self.logger.debug(f"Saved song request from {user}: {req_url}")
            return

        if data.get("chatter_user_name") == "Nightbot":
            await self.handle_nightbot(data)


    # This is kinda a train wreck -- the only way to get all the
    # info we need for logging subs/gift subs/resubs/etc, is to
    # look at the chat notification message (this one) and extract
    # what we want from that. This is weird and irritating, since
    # we do actualy get separate events for subs/resubs/gift
    # subs/etc, but they don't have all the info we need.
    #
    # Sigh.
    async def on_chat_notification(self, data: eventsub.chat.NotificationEvent) -> None:
        self.logger.debug(f"Chat notification received: {data}")

        if data["chatter_is_anonymous"]:
            chatter = "AnAnonymousGifter"
        else:
            chatter = data["chatter_user_name"]

        if data["sub_gift"] is not None:
            gifter = chatter
            recipient = data["sub_gift"]["recipient_user_name"]
            tier = int(data["sub_gift"]["sub_tier"])
            months = 0
            event_type = "subscription.gift"
        elif data["sub"] is not None:
            gifter = ""
            recipient = chatter
            tier = int(data["sub"]["sub_tier"])
            months = 1
            event_type = "subscription.new"
        elif data["resub"] is not None:
            gifter = ""
            recipient = chatter
            tier = int(data["resub"]["sub_tier"])
            months = data["resub"]["cumulative_months"] or 0
            event_type = "subscription.resub"
        else:
            return

        if months == 0:
            sub_str = "Sub"
        else:
            sub_str = f"Sub #{months}"

        value = SUB_VALUES[tier]

        self.logger.info(f"output sub: {value} for {recipient}")
        printsupport(ts=now(), gifter=gifter, supporter=recipient, type=sub_str, amount=value)
        await dispatch_event(event_type, dict(data))

    # async def on_cheer(self, data: eventsub.bits.CheerEvent) -> None:
    #     # print(type(data))
    #     self.logger.debug(f"Cheer received: {data}")
    #     self.logger.info(f"output cheer: {data['bits']} for {data['user_name'] or 'Unknown'}")
    #     printsupport(ts=now(), supporter=data["user_name"] or "Unknown", type="Bits", amount=data["bits"] / 100.0)

    async def on_bits_use(self, data: eventsub.bits.BitsEvent) -> None:
        self.logger.debug(f"Bits use received: {data}")
        self.logger.info(f"output bit use: {data['bits']} for {data['user_name'] or 'Unknown'}")
        printsupport(ts=now(), supporter=data["user_name"]
                     or "Unknown", type="Bits", amount=data["bits"] / 100.0)

    # async def on_points_automatic_reward_redemption_add_v2(self, data: eventsub.interaction.AutomaticRewardRedemptionAddEventV2) -> None:
    #     self.logger.debug(f"Points automatic reward redemption add received: {data}")

    #     user = data["user_name"] or "Unknown"
    #     reward = data["reward"]

    #     if reward["type"] not in AUTOMATIC_REWARD_COSTS:
    #         return

    #     cost = AUTOMATIC_REWARD_COSTS[reward["type"]] / 100.0

    #     self.logger.info(f"output redemption: {cost} for {user}")
    #     printsupport(ts=now(), supporter=user, type="Bits", amount=cost)

    async def on_hype_train_begin(self, data: eventsub.interaction.HypeTrainEvent) -> None:
        self.logger.debug(f"Hype train begin received: {data}")
        self.logger.info(f"output hype train begin")
        out("=== HYPE TRAIN BEGIN ===")
        await dispatch_event("hype_train.begin", dict(data))

    # async def on_hype_train_progress(self, data: eventsub.interaction.HypeTrainEvent):
    #     log(f"INFO: Hype train progress received: {data}")

    async def on_hype_train_end(self, data: eventsub.interaction.HypeTrainEndEvent) -> None:
        self.logger.debug(f"Hype train end received: {data}")
        self.logger.info(f"output hype train end (level={data['level']}, total={data['total']})")
        out(f"=== HYPE TRAIN END (level={data['level']}, total={data['total']}) ===")
        await dispatch_event("hype_train.end", dict(data))


    # async def on_ad_break_begin(self, data: eventsub.streams.AdBreakBeginEvent):
    #     self.logger.debug(f"Ad break begin received: {data}")

    # Incoming raid (for now, don't log outgoing raids)
    async def on_raid(self, data: eventsub.streams.RaidEvent) -> None:
        self.logger.debug(f"Raid received: {data}")
        assert self.user is not None
        if data["from_broadcaster_user_id"] == self.user.id:
            return

        from_user = data["from_broadcaster_user_name"]
        to_user = data["to_broadcaster_user_name"]
        viewers = data["viewers"]

        self.logger.info(f"output raid: {viewers} from {from_user}")
        printsupport(ts=now(), supporter=from_user, type=f"Raid - {viewers}", amount=0.0)
        await dispatch_event("raid", dict(data))


async def start(args: argparse.Namespace, creds: Dict[str, str]|None, logger: logging.Logger) -> None:
    if creds is None:
        raise ValueError("No credentials specified")

    tokens = get_token(args.token_file)
    climode = True if args.environment == 'localdev' else False

    logger.info(f"Starting Twitch backend")
    client = OngWatch_Twitch(client_id=creds['client_id'], client_secret=creds['client_secret'],
                      botargs=args, logger=logger, socket_debug=True, reconnect=True, cli=climode)

    try:
        await client.start(access_token=tokens['token'], refresh_token=tokens["refresh"], reconnect=True)
    except HTTPException as e:
        logger.error(f"Unable to connect to twitch, HTTP error: {e}")
        raise
    except Exception as e:
        logger.error(f"exception: {e}")
        raise

    # Close the client after the try/except block
    try:
        await asyncio.wait_for(client.close(), timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("Timeout while closing Twitch client")
