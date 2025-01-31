# See https://twitchpy.readthedocs.io/ for docs

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from tdvutil import ppretty
from tdvutil.argparse import CheckFile
from twitch import Client
from twitch.types import eventsub

from _ongwatch.util import log, now, out, printsupport

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
        return json.load(f)

class OngWatch_Twitch(Client):
    botargs: argparse.Namespace

    def __init__(self, client_id: str, client_secret: str, **options) -> None:
        if "botargs" in options:
            self.botargs = options["botargs"]

        super().__init__(client_id, client_secret, **options)

    # @staticmethod
    # async def on_error(event_name: str, error: Exception, /, *args: Any, **kwargs: Any) -> None:
    #     log(f"INFO: Error: {error}")

    # async def setup_hook(self) -> None:
    #     """Called when the client is setting up"""
    #     log("INFO: Setting up client")

    async def on_connect(self) -> None:
        log("TW: Connected to Twitch")

    async def on_disconnect(self) -> None:
        log("TW: Disconnected from Twitch")

    async def on_ready(self) -> None:
        """Called when the client is ready."""
        log("TW: Client is ready")
        log(f"TW: User: {self.user.display_name} ({self.user.id})")
        log(f"TW: channel liveness: {await self.channel.stream.get_live()}")

        # total_subs = await self.channel.get_total_subscriptions()
        # total_pts = await self.channel.get_subscription_points()
        # log(f"Subscriptions: {total_subs} ({total_pts} pts)")

        log("TW: Listening for events")

    # Only happens if socket_debug is true
    async def on_socket_raw_receive(self, data: Any) -> None:
        log(f"TW: Socket raw receive: {data}")

    async def on_stream_online(self, data: eventsub.streams.StreamOnlineEvent):
        log(f"TW: Stream online received: {data}")
        out(f"=== ONLINE (type={data["type"]} @ {data["started_at"]} ===")

    async def on_stream_offline(self, data: eventsub.streams.StreamOfflineEvent):
        log(f"TW: Stream offline received: {data}")
        out("=== OFFLINE ===")

    async def on_chat_message(self, data: eventsub.chat.MessageEvent):
        if self.botargs.show_messages:
            log(f"TW: Chat message received: {data}")

    # This is kinda a train wreck -- the only way to get all the
    # info we need for logging subs/gift subs/resubs/etc, is to
    # look at the chat notification message (this one) and extract
    # what we want from that. This is weird and irritating, since
    # we do actualy get separate events for subs/resubs/gift
    # subs/etc, but they don't have all the info we need.
    #
    # Sigh.
    async def on_chat_notification(self, data: eventsub.chat.NotificationEvent):
        log(f"TW: Chat notification received: {data}")

        if data["chatter_is_anonymous"]:
            chatter = "AnAnonymousGifter"
        else:
            chatter = data["chatter_user_name"]

        if data["sub_gift"] is not None:
            gifter = chatter
            recipient = data["sub_gift"]["recipient_user_name"]
            tier = int(data["sub_gift"]["sub_tier"])
            months = 0
        elif data["sub"] is not None:
            gifter = ""
            recipient = chatter
            tier = int(data["sub"]["sub_tier"])
            months = 1
        elif data["resub"] is not None:
            gifter = ""
            recipient = chatter
            tier = int(data["resub"]["sub_tier"])
            months = data["resub"]["cumulative_months"] or 0
        else:
            return

        if months == 0:
            sub_str = "Sub"
        else:
            sub_str = f"Sub #{months}"

        value = SUB_VALUES[tier]

        printsupport(ts=now(), gifter=gifter, supporter=recipient, type=sub_str, amount=value)

    async def on_cheer(self, data: eventsub.bits.CheerEvent):
        # print(type(data))
        log(f"TW: Cheer received: {data}")
        printsupport(ts=now(), supporter=data["user_name"] or "Unknown", type="Bits", amount=data["bits"] / 100.0)


    async def on_points_automatic_reward_redemption_add(self, data: eventsub.interaction.AutomaticRewardRedemptionAddEvent):
        log(f"TW: Points automatic reward redemption add received: {data}")

        user = data["user_name"] or "Unknown"
        reward = data["reward"]

        if reward["type"] not in AUTOMATIC_REWARD_COSTS:
            return

        cost = AUTOMATIC_REWARD_COSTS[reward["type"]] / 100.0

        printsupport(ts=now(), supporter=user, type="Bits", amount=cost)


    async def on_hype_train_begin(self, data: eventsub.interaction.HypeTrainEvent):
        log(f"TW: Hype train begin received: {data}")
        out("=== HYPE TRAIN BEGIN ===")

    # async def on_hype_train_progress(self, data: eventsub.interaction.HypeTrainEvent):
    #     log(f"INFO: Hype train progress received: {data}")

    async def on_hype_train_end(self, data: eventsub.interaction.HypeTrainEndEvent):
        log(f"TW: Hype train end received: {data}")
        out(f"=== HYPE TRAIN END (level={data['level']}, total={data['total']}) ===")

    # async def on_ad_break_begin(self, data: eventsub.streams.AdBreakBeginEvent):
    #     log(f"INFO: Ad break begin received: {data}")

    # Incoming raid (for now, don't log outgoing raids)
    async def on_raid(self, data: eventsub.streams.RaidEvent):
        log(f"TW: Raid received: {data}")
        if data["from_broadcaster_user_id"] == self.user.id:
            return

        from_user = data["from_broadcaster_user_name"]
        to_user = data["to_broadcaster_user_name"]
        viewers = data["viewers"]

        printsupport(ts=now(), supporter=from_user, type=f"Raid - {viewers}", amount=0.0)


async def start(args: argparse.Namespace, creds: Dict[str, str]) -> None:
    tokens = get_token(args.token_file)

    log(f"Starting SE backend")

    client = OngWatch_Twitch(client_id=creds['client_id'], client_secret=creds['client_secret'],
                      botargs=args, socket_debug=args.debug_socket, reconnect=True)
    await client.start(access_token=tokens['token'], refresh_token=tokens["refresh"], reconnect=True)
