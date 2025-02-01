#!/usr/bin/env python
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

import _ongwatch.streamelements as streamelements
import _ongwatch.streamlabs as streamlabs
import _ongwatch.twitch as twitch
from _ongwatch.util import log


def get_credentials(cfgfile: Path, subsystem: str, environment: str) -> Dict[str, str]:
    log(f"loading config from {cfgfile}")
    config = toml.load(cfgfile)

    try:
        return config[subsystem][environment]
    except KeyError:
        log(f"ERROR: no configuration for streamelements.{environment} in credentials file")
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Share to discord some of the stream things that have happened")

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

    # parser.add_argument(
    #     "--auth-only", "--auth",
    #     default=False,
    #     action="store_true",
    #     help="only authenticate, then exit"
    # )

    parser.add_argument(
        "--environment", "--env",
        type=str,
        default="test",
        help="environment to use"
    )

    # FIXME: the following should probably be per-backend
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


async def main() -> int:
    # make sure our output streams are properly encoded so that we can
    # not screw up Frédéric Chopin's name and such.
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding="utf-8", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding="utf-8", line_buffering=True)

    args = parse_args()

    log("INFO: Ongwatch is in startup")

    # creds = get_credentials(args.credentials_file, args.environment)
    # tokens = get_token(args.token_file)

    log("INFO: Ongwatch is in startup")
    # print(f"tokens: {tokens}")
    # print(f"creds: {creds}")

    tasks: list[asyncio.Task] = []

    tw_creds = get_credentials(args.credentials_file, "twitch", args.environment)
    tasks.append(asyncio.create_task(twitch.start(args, tw_creds)))

    se_creds = get_credentials(args.credentials_file, "streamelements", args.environment)
    tasks.append(asyncio.create_task(streamelements.start(args, se_creds)))

    sl_creds = get_credentials(args.credentials_file, "streamlabs", args.environment)
    tasks.append(asyncio.create_task(streamlabs.start(args, sl_creds)))

    # client = OngWatch(client_id=creds['client_id'], client_secret=creds['client_secret'],
    #                   botargs=args, socket_debug=args.debug_socket)

    # FIXME: what's the right way to exit cleanly(ish)?
    # client.run(access_token=tokens['token'], refresh_token=tokens["refresh"], reconnect=True)

    await asyncio.gather(*tasks)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
