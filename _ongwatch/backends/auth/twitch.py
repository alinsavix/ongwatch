import argparse
import asyncio
import logging
from contextlib import suppress
from pathlib import Path
from typing import Any, Dict

from twitchio import Client
from twitchio.authentication import UserTokenPayload
from twitchio.authentication.scopes import Scopes as TIOScopes
from twitchio.web import AiohttpAdapter

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
    "user:bot",
    "user:read:chat",
    "channel:read:ads",
    "user:read:moderated_channels",
    "user:read:emotes",
    "moderator:read:unban_requests",
    "moderator:read:suspicious_users",
])


def _auth_callback_domain(args: argparse.Namespace, creds: Dict[str, str]) -> str:
    return (
        getattr(args, "auth_callback_domain", None)
        or creds.get("auth_callback_domain")
        or creds.get("auth_host")
        or "localhost"
    )


def _auth_callback_port(args: argparse.Namespace, creds: Dict[str, str]) -> int:
    raw_port = (
        getattr(args, "auth_callback_port", None)
        or creds.get("auth_callback_port")
        or creds.get("auth_port")
        or 4343
    )

    try:
        port = int(raw_port)
    except (TypeError, ValueError) as exc:
        raise ValueError("Twitch auth callback port must be an integer") from exc

    if not 1 <= port <= 65535:
        raise ValueError("Twitch auth callback port must be between 1 and 65535")

    return port


def _tio_tokens_path(env: str) -> Path:
    return Path.cwd() / f".tio.tokens.{env}.json"


async def auth(args: argparse.Namespace, creds: Dict[str, str] | None, logger: logging.Logger) -> bool:
    if creds is None:
        raise ValueError("No credentials specified")

    env: str = args.environment
    tokens_path = _tio_tokens_path(env)

    host = _auth_callback_domain(args, creds)
    port = _auth_callback_port(args, creds)
    domain = creds.get("auth_domain")  # optional; enables https + external URL

    adapter: AiohttpAdapter[Any] = AiohttpAdapter(host=host, port=port, domain=domain)

    done = asyncio.Event()

    class AuthClient(Client):
        async def event_oauth_authorized(self, payload: UserTokenPayload) -> None:
            await super().event_oauth_authorized(payload)
            logger.info(f"Authorized user_id={payload.user_id}")
            done.set()

        async def save_tokens(self, path: str | None = None, /) -> None:
            await super().save_tokens(path or str(tokens_path))

    client = AuthClient(
        client_id=creds["client_id"],
        client_secret=creds["client_secret"],
        adapter=adapter,
    )

    visit_url = adapter.get_authorization_url(scopes=USER_SCOPES)

    print(f"\nVisit this URL in your browser to authorize:\n  {visit_url}\n")

    async with client:
        start_task = asyncio.create_task(client.start(load_tokens=False))
        try:
            await done.wait()
        finally:
            await client.close()
            with suppress(asyncio.CancelledError):
                await start_task

    print(f"\nSuccess, tokens written to {tokens_path}")
    return True
