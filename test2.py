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

import toml
import pytz
from tdvutil import ppretty
from tdvutil.argparse import CheckFile
from twitch import Client
from twitch.types import eventsub


def log(msg: str) -> None:
    print(msg, file=sys.stderr)
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
    print(f"{ts_str}\t\t{gifter}\t{supporter}\t{type}\t${amount}\tna\t{comment}")


class OngWatch(Client):
    botargs: argparse.Namespace

    def __init__(self, client_id: str, client_secret: str, **options) -> None:
        if "botargs" in options:
            self.botargs = options["botargs"]

        super().__init__(client_id, client_secret, **options)

    # @staticmethod
    # async def on_error(event_name: str, error: Exception, /, *args: Any, **kwargs: Any) -> None:
    #     log(f"INFO: Error: {error}")

    async def setup_hook(self) -> None:
        """Called when the client is setting up"""
        log("INFO: Setting up client")

    async def on_connect(self) -> None:
        log("INFO: Connected to Twitch")

    async def on_disconnect(self) -> None:
        log("INFO: Disconnected from Twitch")

    async def on_ready(self) -> None:
        """Called when the client is ready."""
        log("INFO: Client is ready")
        log(f"INFO: User: {self.user.display_name} ({self.user.id})")
        # print(ppretty(self.channel))
        # print(ppretty(self.total_subscription_cost))
        # emotes = await self.get_global_emotes()
        # cheermotes = await self.get_global_cheermotes()

        log(f"channel liveness: {await self.channel.stream.get_live()}")
        # await self.channel.stream.create_marker()

        total_subs = await self.channel.get_total_subscriptions()
        total_pts = await self.channel.get_subscription_points()
        log(f"Subscriptions: {total_subs} ({total_pts} pts)")

        # x = self.channel.fetch_banned_users()
        # async for banned in x:
        #     print(ppretty(banned))

        # x = self.channel.fetch_subscriptions()
        # async for sub in x:
        #     print(ppretty(sub))

        # x = self.channel.fetch_videos(video_type="archive")
        # async for video in x:
        #     print(ppretty(video))

        # FIXME: doesn't work, maybe open a bug
        # x = self.channel.fetch_clips()
        # async for clip in x:
        #     print(clip)

        # FIXME: weird, seems to be List[List[mod]] instead of List[mod]
        # (might be because of the paging thing)
        # x = self.channel.fetch_moderators()
        # async for m in x:
        #     for moderator in m:
        #         print(moderator)

        # x = await self.channel.get_editors()
        # print(x)

        # x = self.channel.fetch_vips()
        # async for vip in x:
        #     print(vip)

        # FIXME: doesn't work, maybe open bug
        # x = await self.channel.get_bits_leaderboard(period="week")
        # print(x)

        # FIXME: returns an empty list?
        # x = self.channel.fetch_hype_trains()
        # async for train in x:
        #     print(train)

        # x = await self.channel.get_rewards()
        # for xx in x:
        #     print(xx)

        # FIXME: doesn't work, maybe open bug
        # x = self.channel.fetch_reward_redemptions(status="unfulfilled", reward_id="POINTSAWAY")
        # async for redemptions in x:
        #     print(redemptions)

        # x = self.channel.fetch_predictions()
        # async for prediction in x:
        #     print(prediction)

        # x = self.channel.fetch_polls()
        # async for poll in x:
        #     print(poll)

        # print(self.channel.stream)

        # print(await self.channel.chat.get_settings())

        # print(await self.channel.chat.get_total_chatters())

        # x = self.channel.chat.fetch_chatters()
        # async for chatters in x:
        #     print(chatters)

        # x = await self.channel.chat.get_emotes()
        # print(x)

        # x = await self.channel.chat.get_cheermotes()
        # print(x)

        # x = await self.channel.chat.get_badges()
        # print(x)

        # x = await self.channel.chat.get_automod_settings()
        # print(x)

        # x = self.channel.chat.fetch_blocked_terms()
        # async for term in x:
        #     print(term)

        # FIXME: doesn't work, maybe open bug
        # x = self.channel.stream.fetch_schedule()
        # async for schedule in x:
        #     print(schedule)

        # x = await self.channel.stream.get_ad_schedule()
        # print(x)

        # print(self.total_subscription_cost, self.max_subscription_cost)

    async def on_socket_raw_receive(self, data: Any) -> None:
        log(f"INFO: Socket raw receive: {data}")

    async def on_channel_update(self, data: eventsub.channels.ChannelUpdateEvent):
        log(f"INFO: Channel update received: {data}")

    async def on_user_update(self, data: eventsub.users.UserUpdateEvent):
        log(f"INFO: User update received: {data}")

    async def on_stream_online(self, data: eventsub.streams.StreamOnlineEvent):
        log(f"INFO: Stream online received: {data}")

    async def on_stream_offline(self, data: eventsub.streams.StreamOfflineEvent):
        log(f"INFO: Stream offline received: {data}")

    async def on_chat_message(self, data: eventsub.chat.MessageEvent):
        if self.botargs.show_messages:
            log(f"INFO: Chat message received: {data}")

    async def on_chat_notification(self, data: eventsub.chat.NotificationEvent):
        log(f"INFO: Chat notification received: {data}")

    async def on_chat_settings_update(self, data: eventsub.chat.SettingsUpdateEvent):
        log(f"INFO: Chat settings update received: {data}")

    async def on_cheer(self, data: eventsub.bits.CheerEvent):
        # print(type(data))
        # log(f"INFO: Cheer received: {data}")
        printsupport(ts=now(), supporter=data["user_name"] or "Unknown", type="Bits", amount=data["bits"] / 100.0)


    async def on_automod_settings_update(self, data: eventsub.moderation.AutomodSettingsUpdateEvent):
        log(f"INFO: Automod settings update received: {data}")

    # async def on_automod_terms_update(self, data: eventsub.moderation.AutomodTermsUpdateEvent):
    #     log(f"INFO: Automod action received: {data}")

    # async def on_ban(self, data: eventsub.moderation.BanEvent):
    #     log(f"INFO: Ban received: {data}")

    # async def on_unban(self, data: eventsub.moderation.UnbanEvent):
    #     log(f"INFO: Unban received: {data}")

    async def on_channel_moderate(self, data: eventsub.moderation.ModerateEvent):
        log(f"INFO: Channel moderate received: {data}")

    async def on_moderator_add(self, data: eventsub.moderation.ModeratorAddEvent):
        log(f"INFO: Moderator add received: {data}")

    async def on_moderator_remove(self, data: eventsub.moderation.ModeratorRemoveEvent):
        log(f"INFO: Moderator remove received: {data}")

    async def on_follow(self, data: eventsub.channels.FollowEvent):
        log(f"INFO: Follow received: {data}")

    # Only for new subs (or long expired subs)
    async def on_subscribe(self, data: eventsub.channels.SubscribeEvent):
        log(f"INFO: Subscribe received: {data}")

    async def on_subscription_end(self, data: eventsub.channels.SubscriptionEndEvent):
        log(f"INFO: Subscription end received: {data}")

    async def on_subscription_gift(self, data: eventsub.channels.SubscriptionGiftEvent):
        log(f"INFO: Subscription gift received: {data}")

    async def on_subscription_message(self, data: eventsub.channels.SubscriptionMessageEvent):
        log(f"INFO: Subscription message received: {data}")

    async def on_points_automatic_reward_redemption_add(self, data: eventsub.interaction.AutomaticRewardRedemptionAddEvent):
        log(f"INFO: Points automatic reward redemption add received: {data}")

    async def on_points_reward_add(self, data: eventsub.interaction.PointRewardEvent):
        log(f"INFO: Points reward add received: {data}")

    async def on_points_reward_update(self, data: eventsub.interaction.PointRewardEvent):
        log(f"INFO: Points reward update received: {data}")

    async def on_points_reward_remove(self, data: eventsub.interaction.PointRewardEvent):
        log(f"INFO: Points reward remove received: {data}")

    async def on_points_reward_redemption_add(self, data: eventsub.interaction.RewardRedemptionEvent):
        log(f"INFO: Points reward redemption add received: {data}")

    async def on_points_reward_redemption_update(self, data: eventsub.interaction.RewardRedemptionEvent):
        log(f"INFO: Points reward redemption update received: {data}")

    async def on_points_reward_redemption_remove(self, data: eventsub.interaction.PointRewardEvent):
        log(f"INFO: Points reward redemption remove received: {data}")

    async def on_poll_begin(self, data: eventsub.interaction.PollBeginEvent):
        log(f"INFO: Poll begin received: {data}")

    async def on_poll_progress(self, data: eventsub.interaction.PollProgressEvent):
        log(f"INFO: Poll progress received: {data}")

    async def on_poll_end(self, data: eventsub.interaction.PollEndEvent):
        log(f"INFO: Poll end received: {data}")

    async def on_prediction_begin(self, data: eventsub.interaction.PredictionBeginEvent):
        log(f"INFO: Prediction begin received: {data}")

    async def on_prediction_progress(self, data: eventsub.interaction.PredictionProgressEvent):
        log(f"INFO: Prediction progress received: {data}")

    async def on_prediction_lock(self, data: eventsub.interaction.PredictionLockEvent):
        log(f"INFO: Prediction lock received: {data}")

    async def on_prediction_end(self, data: eventsub.interaction.PredictionEndEvent):
        log(f"INFO: Prediction end received: {data}")

    async def on_hype_train_begin(self, data: eventsub.interaction.HypeTrainEvent):
        log(f"INFO: Hype train begin received: {data}")

    async def on_hype_train_progress(self, data: eventsub.interaction.HypeTrainEvent):
        log(f"INFO: Hype train progress received: {data}")

    async def on_hype_train_end(self, data: eventsub.interaction.HypeTrainEndEvent):
        log(f"INFO: Hype train end received: {data}")

    async def on_ad_break_begin(self, data: eventsub.streams.AdBreakBeginEvent):
        log(f"INFO: Ad break begin received: {data}")

    async def on_raid(self, data: eventsub.streams.RaidEvent):
        log(f"INFO: Raid received: {data}")



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

    log("INFO: In startup")
    print(f"tokens: {tokens}")
    print(f"creds: {creds}")

    client = OngWatch(client_id=creds['client_id'], client_secret=creds['client_secret'], botargs=args, socket_debug=args.debug_socket)
    client.run(access_token=tokens['token'], refresh_token=tokens["refresh"], reconnect=True)

    return 0
    # client.close()
    # return asyncio.run(run(args, creds))


if __name__ == "__main__":
    sys.exit(main())
