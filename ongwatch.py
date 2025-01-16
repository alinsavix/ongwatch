#!/usr/bin/env python
# See https://twitchpy.readthedocs.io/ for docs

import argparse
import asyncio
import datetime
import io
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

import pytz
import toml
from tdvutil import ppretty
from tdvutil.argparse import CheckFile
from twitch import Client
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

# FIXME: use real logging ffs
def out(msg: str) -> None:
    print(timestr_est(now()), msg, file=sys.stdout)
    sys.stdout.flush()

    log(msg)


def log(msg: str) -> None:
    print(timestr_est(now()), msg, file=sys.stderr)
    sys.stderr.flush()


def now() -> int:
    return int(time.time())


def timestr_est(ts: int) -> str:
    utc_time = datetime.datetime.fromtimestamp(ts, datetime.UTC)
    eastern_zone = pytz.timezone('US/Eastern')
    eastern_time = utc_time.replace(tzinfo=pytz.utc).astimezone(eastern_zone)
    return eastern_time.strftime("%Y-%m-%d %H:%M:%S")


def printsupport(ts: int, gifter: str = "", supporter: str = "", type: str = "", amount: float = 0.0, comment: str = ""):
    ts_str = timestr_est(ts)
    outstr = f"{ts_str}\t\t{gifter}\t{supporter}\t{type}\t${amount:0.2f}\tna\t{comment}"
    print(outstr, file=sys.stdout)
    sys.stdout.flush()

    # FIXME: super sloppy
    print(outstr, file=sys.stderr)
    sys.stderr.flush()


class OngWatch(Client):
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
        log("INFO: Connected to Twitch")

    async def on_disconnect(self) -> None:
        log("INFO: Disconnected from Twitch")

    async def on_ready(self) -> None:
        """Called when the client is ready."""
        log("INFO: Client is ready")
        log(f"INFO: User: {self.user.display_name} ({self.user.id})")
        # log(f"INFO: channel liveness: {await self.channel.stream.get_live()}")

        # total_subs = await self.channel.get_total_subscriptions()
        # total_pts = await self.channel.get_subscription_points()
        # log(f"Subscriptions: {total_subs} ({total_pts} pts)")

        log("INFO: Listening for events")

    # Only happens if socket_debug is true
    async def on_socket_raw_receive(self, data: Any) -> None:
        log(f"INFO: Socket raw receive: {data}")

    async def on_stream_online(self, data: eventsub.streams.StreamOnlineEvent):
        log(f"INFO: Stream online received: {data}")
        out(f"=== ONLINE (type={data["type"]} @ {data["started_at"]} ===")

    async def on_stream_offline(self, data: eventsub.streams.StreamOfflineEvent):
        log(f"INFO: Stream offline received: {data}")
        out("=== OFFLINE ===")

    async def on_chat_message(self, data: eventsub.chat.MessageEvent):
        if self.botargs.show_messages:
            log(f"INFO: Chat message received: {data}")

    # This is kinda a train wreck -- the only way to get all the
    # info we need for logging subs/gift subs/resubs/etc, is to
    # look at the chat notification message (this one) and extract
    # what we want from that. This is weird and irritating, since
    # we do actualy get separate events for subs/resubs/gift
    # subs/etc, but they don't have all the info we need.
    #
    # Sigh.
    async def on_chat_notification(self, data: eventsub.chat.NotificationEvent):
        log(f"INFO: Chat notification received: {data}")

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
        log(f"INFO: Cheer received: {data}")
        printsupport(ts=now(), supporter=data["user_name"] or "Unknown", type="Bits", amount=data["bits"] / 100.0)


    async def on_points_automatic_reward_redemption_add(self, data: eventsub.interaction.AutomaticRewardRedemptionAddEvent):
        log(f"INFO: Points automatic reward redemption add received: {data}")

        user = data["user_name"] or "Unknown"
        reward = data["reward"]

        if reward["type"] not in AUTOMATIC_REWARD_COSTS:
            return

        cost = AUTOMATIC_REWARD_COSTS[reward["type"]] / 100.0

        printsupport(ts=now(), supporter=user, type="Bits", amount=cost)


    async def on_hype_train_begin(self, data: eventsub.interaction.HypeTrainEvent):
        log(f"INFO: Hype train begin received: {data}")
        out("=== HYPE TRAIN BEGIN ===")

    # async def on_hype_train_progress(self, data: eventsub.interaction.HypeTrainEvent):
    #     log(f"INFO: Hype train progress received: {data}")

    async def on_hype_train_end(self, data: eventsub.interaction.HypeTrainEndEvent):
        log(f"INFO: Hype train end received: {data}")
        out(f"=== HYPE TRAIN END (level={data['level']}, total={data['total']}) ===")

    # async def on_ad_break_begin(self, data: eventsub.streams.AdBreakBeginEvent):
    #     log(f"INFO: Ad break begin received: {data}")

    # Incoming raid (for now, don't log outgoing raids)
    async def on_raid(self, data: eventsub.streams.RaidEvent):
        log(f"INFO: Raid received: {data}")
        if data["from_broadcaster_user_id"] == self.user.id:
            return

        from_user = data["from_broadcaster_user_name"]
        to_user = data["to_broadcaster_user_name"]
        viewers = data["viewers"]

        printsupport(ts=now(), supporter=from_user, type=f"Raid - {viewers}", amount=0.0)


def get_credentials(cfgfile: Path, environment: str) -> Dict[str, str]:
    log(f"loading config from {cfgfile}")
    config = toml.load(cfgfile)

    try:
        return config["eventbot"][environment]
    except KeyError:
        log(f"ERROR: no configuration for eventbot.{environment} in credentials file")
        sys.exit(1)


def get_token(token_file: Path) -> Dict[str, str]:
    with open(token_file, 'r') as f:
        return json.load(f)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Share to discord some of the changes ojbpm has detected")

    parser.add_argument(
        "--credentials-file", "-c",
        type=Path,
        default=None,
        action=CheckFile(must_exist=True),
        help="file with discord credentials"
    )

    parser.add_argument(
        "--token-file", "-t",
        type=Path,
        default=None,
        help="file to store twitch credentials"
    )

    parser.add_argument(
        "--auth-only", "--auth",
        default=False,
        action="store_true",
        help="only authenticate, then exit"
    )

    parser.add_argument(
        "--environment", "--env",
        type=str,
        default="test",
        help="environment to use"
    )

    parser.add_argument(
        "--debug-socket",
        default=False,
        action="store_true",
        help="output raw websocket messages as received"
    )

    parser.add_argument(
        "--show-messages",
        default=False,
        action="store_true",
        help="show all messages"
    )

    # parser.add_argument(
    #     "--dbfile",
    #     type=Path,
    #     default=None,
    #     help="database file to use"
    # )

    # parser.add_argument(
    #     "--debug-queries",
    #     default=False,
    #     action="store_true",
    #     help="print all queries to stderr",
    # )

    parsed_args = parser.parse_args()

    if parsed_args.credentials_file is None:
        parsed_args.credentials_file = Path(__file__).parent / "credentials.toml"

    if parsed_args.token_file is None:
        parsed_args.token_file = Path(__file__).parent / "user_token.json"

    return parsed_args


def main() -> int:
    # make sure our output streams are properly encoded so that we can
    # not screw up Frédéric Chopin's name and such.
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding="utf-8", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding="utf-8", line_buffering=True)

    args = parse_args()

    creds = get_credentials(args.credentials_file, args.environment)
    tokens = get_token(args.token_file)

    log("INFO: Ongwatch is in startup")
    # print(f"tokens: {tokens}")
    # print(f"creds: {creds}")

    client = OngWatch(client_id=creds['client_id'], client_secret=creds['client_secret'], botargs=args, socket_debug=args.debug_socket)

    # FIXME: what's the right way to exit cleanly(ish)?
    client.run(access_token=tokens['token'], refresh_token=tokens["refresh"], reconnect=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
