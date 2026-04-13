import argparse
import json
import logging
from pathlib import Path
from typing import Dict

from twitchio import Client
from twitchio.authentication.scopes import Scopes as TIOScopes

USER_SCOPES = TIOScopes([
    "bits:read",
    "channel:read:subscriptions",
    "channel:read:hype_train",
    "channel:read:redemptions",
    "channel:read:charity",
    "moderation:read",
    "channel:read:editors",
    "channel:read:goals",
    "channel:read:polls",
    "channel:read:predictions",
    "moderator:read:chat_settings",
    "moderator:read:blocked_terms",
    "moderator:read:chat_messages",
    "moderator:read:warnings",
    "channel:read:vips",
    "moderator:read:chatters",
    "moderator:read:shield_mode",
    "moderator:read:automod_settings",
    "moderator:read:followers",
    "moderator:read:shoutouts",
    "channel:bot",
    "user:read:chat",
    "channel:read:ads",
    "user:read:moderated_channels",
    "user:read:emotes",
    "moderator:read:unban_requests",
    "moderator:read:suspicious_users",
])


def write_token(token_file: Path, token: Dict[str, str]) -> None:
    with open(token_file, 'w') as f:
        json.dump(token, f)


async def auth(args: argparse.Namespace, creds: Dict[str, str] | None, logger: logging.Logger) -> bool:
    if creds is None:
        raise ValueError("No credentials specified")

    client = Client(client_id=creds['client_id'], client_secret=creds['client_secret'])

    dcf = await client.device_code_flow(scopes=USER_SCOPES)
    print(f'Go to: {dcf.verification_uri}')
    print(f'Enter code: {dcf.user_code}')

    try:
        token = await client.device_code_authorization(
            device_code=dcf.device_code,
            interval=dcf.interval,
        )
    except Exception as e:
        logger.error(f'Failed to authorize: {e}')
        return False

    write_token(args.token_file, {
        'token': token.access_token,
        'refresh': token.refresh_token,
    })
    print(f"\nSuccess, written to {args.token_file}")
    return True
