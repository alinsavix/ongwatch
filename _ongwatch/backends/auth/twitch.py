import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, cast

from tdvutil import ppretty
from twitch import Client
from twitch.errors import HTTPException
from twitch.ext.oauth import DeviceAuthFlow, Scopes

USER_SCOPES: List[str | Scopes] = [
    Scopes.BITS_READ,
    Scopes.CHANNEL_READ_SUBSCRIPTIONS,
    Scopes.CHANNEL_READ_HYPE_TRAIN,
    Scopes.CHANNEL_READ_REDEMPTIONS,
    Scopes.CHANNEL_READ_CHARITY,
    Scopes.MODERATION_READ,
    Scopes.CHANNEL_READ_SUBSCRIPTIONS,
    Scopes.CHANNEL_READ_EDITORS,
    # Scopes.USER_READ_BLOCKED_USERS,
    # Scopes.USER_READ_SUBSCRIPTIONS,
    Scopes.CHANNEL_READ_GOALS,
    Scopes.CHANNEL_READ_POLLS,
    Scopes.CHANNEL_READ_PREDICTIONS,
    Scopes.MODERATOR_READ_CHAT_SETTINGS,
    # Scopes.MODERATOR_READ_BANNED_USERS,
    Scopes.MODERATOR_READ_BLOCKED_TERMS,
    Scopes.MODERATOR_READ_CHAT_MESSAGES,
    Scopes.MODERATOR_READ_WARNINGS,
    Scopes.CHANNEL_READ_VIPS,
    # Scopes.MODERATOR_READ_MODERATORS,  # do we need this?
    Scopes.MODERATOR_READ_CHATTERS,
    Scopes.MODERATOR_READ_SHIELD_MODE,
    Scopes.MODERATOR_READ_AUTOMOD_SETTINGS,
    Scopes.MODERATOR_READ_FOLLOWERS,
    Scopes.MODERATOR_READ_SHOUTOUTS,
    Scopes.CHANNEL_BOT,  # do we need to do something special to use chat?
    # Scopes.USER_BOT,  # how is this different?
    Scopes.USER_READ_CHAT,
    Scopes.CHANNEL_READ_ADS,
    Scopes.USER_READ_MODERATED_CHANNELS,
    Scopes.USER_READ_EMOTES,
    Scopes.MODERATOR_READ_UNBAN_REQUESTS,
    Scopes.MODERATOR_READ_SUSPICIOUS_USERS,
]


# FIXME: dedupe this
def get_token(token_file: Path) -> Dict[str, str]:
    with open(token_file, 'r') as f:
        return cast(Dict[str, str], json.load(f))


class TwitchAuth(Client):
    botargs: argparse.Namespace

    def __init__(self, args: argparse.Namespace, client_id: str, client_secret: str, **options: Any) -> None:
        self.botargs = args
        super().__init__(client_id, client_secret, **options)
        self.auth_flow = DeviceAuthFlow(
            self,
            scopes=USER_SCOPES,
            dispatch=False,
            wrap_run=False
        )

    # async def on_ready(self) -> None:
    #     print('Client is ready!')

    async def custom_auth_flow(self) -> None:
        async with self.auth_flow:
            # Retrieve device code and display the verification URL
            user_code, device_code, expires_in, interval = await self.auth_flow.get_device_code()
            print(f'Verification URL: https://www.twitch.tv/activate?device-code={user_code}')
            expires_in = 30

            # Poll for the authorization and handle token retrieval
            try:
                access_token, refresh_token = \
                    await self.auth_flow.poll_for_authorization(device_code, expires_in, interval)
                print(f'\nAccess Token: {access_token}\nRefresh Token: {refresh_token}')
            except Exception as e:
                print(f'\nERROR: Failed to authorize: {e}')
                sys.exit(1)

        # write the access token and refresh token to a file
        with open(self.botargs.token_file, 'w') as f:
            f.write(json.dumps({'token': access_token, 'refresh': refresh_token}))

        print(f"\nSuccess, written to {self.botargs.token_file}")

    async def run_client(self) -> None:
        await self.custom_auth_flow()


async def auth(args: argparse.Namespace, creds: Dict[str, str] | None, logger: logging.Logger) -> bool:
    if creds is None:
        raise ValueError("No credentials specified")

    tokens = get_token(args.token_file)

    client = TwitchAuth(args, client_id=creds['client_id'], client_secret=creds['client_secret'],
                        logger=logger)

    try:
        await client.run_client()
    except HTTPException as e:
        logger.error(f"Unable to complete auth flow, HTTP error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unable to complete auth flow, unhandled exception: {e}")
        return False

    return True
