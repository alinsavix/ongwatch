#!/usr/bin/env python
import argparse
import asyncio
import datetime
import io
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Tuple

import pytz
import toml
from tdvutil import ppretty
from tdvutil.argparse import CheckFile
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.helper import first
from twitchAPI.oauth import CodeFlow, UserAuthenticationStorageHelper
from twitchAPI.object.eventsub import ChannelCheerEvent, ChannelFollowEvent
from twitchAPI.twitch import AuthScope, Twitch


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


print(timestr_est(1715712000))
def printsupport(ts: int, gifter: str="", supporter: str="", type: str="",amount: float=0.0, comment: str=""):
    ts_str = timestr_est(ts)
    print(f"{ts_str}\t\t{gifter}\t{supporter}\t{type}\t${amount}\tna\t{comment}")


USER_SCOPES = [
    AuthScope.BITS_READ,
    AuthScope.CHANNEL_READ_SUBSCRIPTIONS,
    AuthScope.CHANNEL_READ_HYPE_TRAIN,
    AuthScope.CHANNEL_READ_REDEMPTIONS,
    AuthScope.CHANNEL_READ_CHARITY,
    AuthScope.CHAT_READ,
    AuthScope.MODERATION_READ,
    AuthScope.CHANNEL_SUBSCRIPTIONS,  # I think we want this?
    AuthScope.CHANNEL_READ_EDITORS,
    # AuthScope.USER_READ_BLOCKED_USERS,
    # AuthScope.USER_READ_SUBSCRIPTIONS,
    AuthScope.CHANNEL_READ_GOALS,
    AuthScope.CHANNEL_READ_POLLS,
    AuthScope.CHANNEL_READ_PREDICTIONS,
    AuthScope.MODERATOR_READ_CHAT_SETTINGS,
    AuthScope.MODERATOR_READ_BANNED_USERS,
    AuthScope.MODERATOR_READ_BLOCKED_TERMS,
    AuthScope.MODERATOR_READ_CHAT_MESSAGES,
    AuthScope.MODERATOR_READ_WARNINGS,
    AuthScope.CHANNEL_READ_VIPS,
    AuthScope.MODERATOR_READ_MODERATORS,  # do we need this?
    AuthScope.MODERATOR_READ_CHATTERS,
    AuthScope.MODERATOR_READ_SHIELD_MODE,
    AuthScope.MODERATOR_READ_AUTOMOD_SETTINGS,
    AuthScope.MODERATOR_READ_FOLLOWERS,
    AuthScope.MODERATOR_READ_SHOUTOUTS,
    AuthScope.CHANNEL_BOT,  # do we need ot do something special to use chat?
    # AuthScope.USER_BOT,  # how is this different?
    AuthScope.USER_READ_CHAT,
    AuthScope.CHANNEL_READ_ADS,
    AuthScope.USER_READ_MODERATED_CHANNELS,
    # AuthScope.USER_READ_EMOTES,
    AuthScope.MODERATOR_READ_UNBAN_REQUESTS,
    AuthScope.MODERATOR_READ_SUSPICIOUS_USERS,
]

# async def twitch_setup():
#     global twitch, auth
#     twitch = await Twitch(APP_ID, APP_SECRET)
#     auth = UserAuthenticator(twitch, TARGET_SCOPE, url=MY_URL)
# async def tokens_store(storage_path: Path, token: str, refresh_token: str):
#     with open(storage_path, 'w') as f:
#         json.dump({'token': token, 'refresh': refresh_token}, f)

# class NoTokenAvailable(Exception):
#     pass

# async def tokens_load(storage_path: Path) -> Tuple[str, str]:
#     if not storage_path.exists():
#         raise NoTokenAvailable

#     with open(storage_path, 'r') as f:
#         data = json.load(f)

#     if 'token' not in data or 'refresh' not in data:
#         raise NoTokenAvailable

#     return data['token'], data['refresh']

async def token_create(twitch: Twitch, scopes: list[AuthScope]) -> Tuple[str, str]:
    code_flow = CodeFlow(twitch, scopes)
    code, url = await code_flow.get_code()
    print(f"Please authorize this device: {url}")
    token, refresh = await code_flow.wait_for_auth_complete()

    # print(f"New token: {token}")
    # print(f"New refresh: {refresh}")

    return token, refresh


# async def on_follow(data: ChannelFollowEvent):
#     # our event happened, lets do things with the data we got!
#     # print(f'{data.event.user_name} now follows {data.event.broadcaster_user_name}!')
#     print(f"ChannelFollowEvent: {data.event}")

async def on_cheer(data: ChannelCheerEvent):
    # our event happened, lets do things with the data we got!
    printsupport(ts=now(), supporter=data.event.user_name, type="Bits", amount=data.event.bits / 100.0)

async def on_any(data: Any):
    data_str = ppretty(data, depth=6, str_length=120, ignore=["subscription"])
    print(f"Event of type {str(type(data)).split('.')[-1]}:\n {data_str}")
    sys.stdout.flush()


async def run(args: argparse.Namespace, creds: Dict[str, str]) -> int:
    twitch = await Twitch(creds['client_id'], creds['client_secret'])

    # token_file = Path(__file__).parent / "user_token.json"
    # try:
    #     token, refresh = await tokens_load(token_file)
    #     await twitch.set_user_authentication(token, USER_SCOPES, refresh, validate=True)
    #     print(token, USER_SCOPES, refresh)
    # except NoTokenAvailable:
    #     code_flow = CodeFlow(twitch, USER_SCOPES)
    #     code, url = await code_flow.get_code()
    #     print(url)
    #     token, refresh = await code_flow.wait_for_auth_complete()
    #     await twitch.set_user_authentication(token, USER_SCOPES, refresh, validate=True)
    #     tokens_store(token_file, token, refresh)

    # Is this the right way to do this? iono
    helper = UserAuthenticationStorageHelper(twitch, USER_SCOPES, auth_generator_func=token_create)
    await helper.bind()

    log("We seem healthy!")

    # get the currently logged in user
    user = await first(twitch.get_users())
    log(f"Logged in as {user.display_name} (id {user.id})")

    # create eventsub websocket instance and start the client.
    eventsub = EventSubWebsocket(twitch)
    eventsub.start()

    log("Subscribing to events...")
    # We have to subscribe to the first topic within 10 seconds of eventsub.start() to not be disconnected.
    # await eventsub.listen_channel_follow_v2(user.id, user.id, on_follow)
    # await eventsub.listen_automod_message_hold(user.id, user.id, on_any)  # no auth
    # await eventsub.listen_automod_message_update(user.id, user.id, on_any)
    await eventsub.listen_channel_ad_break_begin(user.id, on_any)
    # await eventsub.listen_channel_ban(user.id, on_any)  # no auth
    await eventsub.listen_channel_charity_campaign_donate(user.id, on_any)
    await eventsub.listen_channel_charity_campaign_progress(user.id, on_any)
    await eventsub.listen_channel_charity_campaign_start(user.id, on_any)
    await eventsub.listen_channel_charity_campaign_stop(user.id, on_any)
    # await eventsub.listen_channel_chat_clear(user.id, on_any)  # no auth
    await eventsub.listen_channel_chat_clear_user_messages(user.id, user.id, on_any)

    # Remember to look up twitchAPI.object.eventsub.ChatMessageFragment sometime
    await eventsub.listen_channel_chat_message(user.id, user.id, on_any)

    await eventsub.listen_channel_chat_message_delete(user.id, user.id, on_any)
    await eventsub.listen_channel_chat_notification(user.id, user.id, on_any)
    await eventsub.listen_channel_chat_settings_update(user.id, user.id, on_any)
    await eventsub.listen_channel_cheer(user.id, on_cheer)
    await eventsub.listen_channel_follow_v2(user.id, user.id, on_any)
    # await eventsub.listen_channel_moderate(user.id, user.id, on_any)  # requires LOTS of permissions
    await eventsub.listen_channel_moderator_add(user.id, on_any)
    await eventsub.listen_channel_moderator_remove(user.id, on_any)
    await eventsub.listen_channel_points_automatic_reward_redemption_add(user.id, on_any)
    await eventsub.listen_channel_points_custom_reward_add(user.id, on_any)
    await eventsub.listen_channel_points_custom_reward_redemption_add(user.id, on_any)
    await eventsub.listen_channel_points_custom_reward_redemption_update(user.id, on_any)
    await eventsub.listen_channel_points_custom_reward_remove(user.id, on_any)
    await eventsub.listen_channel_points_custom_reward_update(user.id, on_any)
    await eventsub.listen_channel_poll_begin(user.id, on_any)
    await eventsub.listen_channel_poll_end(user.id, on_any)
    await eventsub.listen_channel_poll_progress(user.id, on_any)
    await eventsub.listen_channel_prediction_begin(user.id, on_any)
    await eventsub.listen_channel_prediction_end(user.id, on_any)
    await eventsub.listen_channel_prediction_lock(user.id, on_any)
    await eventsub.listen_channel_prediction_progress(user.id, on_any)
    await eventsub.listen_channel_raid(on_any, to_broadcaster_user_id=user.id)
    await eventsub.listen_channel_raid(on_any, from_broadcaster_user_id=user.id)

    await eventsub.listen_channel_shield_mode_begin(user.id, user.id, on_any)
    await eventsub.listen_channel_shield_mode_end(user.id, user.id, on_any)
    await eventsub.listen_channel_shoutout_create(user.id, user.id, on_any)
    await eventsub.listen_channel_shoutout_receive(user.id, user.id, on_any)
    await eventsub.listen_channel_subscribe(user.id, on_any)  # does not include resubs
    await eventsub.listen_channel_subscription_end(user.id, on_any)  # what even is this?
    await eventsub.listen_channel_subscription_gift(user.id, on_any)
    await eventsub.listen_channel_subscription_message(user.id, on_any)
    await eventsub.listen_channel_suspicious_user_message(user.id, user.id, on_any)
    # # await eventsub.listen_channel_unban(user.id, on_any)  # no auth
    # # await eventsub.listen_channel_unban_request_create(user.id, user.id, on_any)  # no auth
    await eventsub.listen_channel_update_v2(user.id, on_any)
    await eventsub.listen_channel_vip_add(user.id, on_any)
    await eventsub.listen_channel_vip_remove(user.id, on_any)
    await eventsub.listen_channel_warning_acknowledge(user.id, user.id, on_any)
    await eventsub.listen_channel_warning_send(user.id, user.id, on_any)
    # # await eventsub.listen_drop_entitlement_grant()   # nope
    # # await eventsub.listen_extension_bits_transaction_create()  # nope
    await eventsub.listen_goal_begin(user.id, on_any)
    await eventsub.listen_goal_end(user.id, on_any)
    await eventsub.listen_goal_progress(user.id, on_any)
    await eventsub.listen_hype_train_begin(user.id, on_any)
    await eventsub.listen_hype_train_end(user.id, on_any)
    await eventsub.listen_hype_train_progress(user.id, on_any)
    await eventsub.listen_stream_offline(user.id, on_any)
    await eventsub.listen_stream_online(user.id, on_any)
    # # await eventsub.listen_user_authorization_grant(user.id, on_any)  # no auth
    # # await eventsub.listen_user_authorization_revoke(user.id, on_any)  # no auth
    await eventsub.listen_user_update(user.id, on_any)
    # # await eventsub.listen_user_whisper_message(user.id, on_any)  # don't want
    # await eventsub.unsubscribe_all()
    # await eventsub.unsubscribe_all_known()


    print("Initialization complete, waiting for stuff to happen...")
    # eventsub will run in its own process
    # so lets just wait for user input before shutting it all down again
    # FIXME: what is a better way to handle this?
    try:
        input('press Enter to shut down...')
    except KeyboardInterrupt:
        pass
    finally:
        # stopping both eventsub as well as gracefully closing the connection to the API
        await eventsub.stop()
        await twitch.close()

    # await twitch.close()
    # print(token, USER_SCOPES, refresh)


def get_credentials(cfgfile: Path, environment: str) -> Dict[str, str]:
    log(f"loading config from {cfgfile}")
    config = toml.load(cfgfile)

    try:
        return config["eventbot"][environment]
    except KeyError:
        log(f"ERROR: no configuration for eventbot.{environment} in credentials file")
        sys.exit(1)


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


    if args.auth_only:
        asyncio.run(token_create(twitch, USER_SCOPES))
        return 0


    log("INFO: In startup")

    return asyncio.run(run(args, creds))




if __name__ == "__main__":
    sys.exit(main())
