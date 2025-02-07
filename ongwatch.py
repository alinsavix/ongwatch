#!/usr/bin/env python
import argparse
import asyncio
import importlib
import io
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Text

from tdvutil import ppretty
from tdvutil.argparse import CheckFile

from _ongwatch.util import get_credentials

# FIXME: generate this dynamically?
BACKEND_LIST = ["twitch", "streamelements", "streamlabs"]

async def do_auth_flow(args: argparse.Namespace, backend: str, logger: logging.Logger) -> int:
    logger.setLevel(logging.WARNING)  # quiet things down
    creds = get_credentials(args.credentials_file, backend, args.environment)
    if creds is None:
        logger.error(f"No credentials found for {backend}")
        return 1

    try:
        module = importlib.import_module(f"_ongwatch.auth.{backend}")
    except ModuleNotFoundError as e:
        logger.error(f"No such backend '{backend}': {e}")
        return 1

    if "auth" not in dir(module):
        logger.error(f"No auth handler available for Backend '{backend}'")
        return 1

    return await module.auth(args, creds, logging.getLogger(args.auth))


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

    # FIXME: deal with this better -- it's twitch only (for now?)
    parser.add_argument(
        "--token-file", "-t",
        type=Path,
        default=None,
        help="file to store twitch credentials"
    )

    parser.add_argument(
        "--auth",
        type=str,
        default=None,
        help="do authentication flow for a given backend"
    )

    parser.add_argument(
        "--environment", "--env",
        type=str,
        default="test",
        help="environment to use"
    )

    # FIXME: the following should probably be per-backend
    parser.add_argument(
        "--debug-backend",
        type=str,
        action="append",
        default=[],
        help="enable debug logging for named backend"
    )

    parser.add_argument(
        "--disable-backend",
        type=str,
        action="append",
        default=[],
        help="disable named backend"
    )

    parsed_args = parser.parse_args()

    if parsed_args.credentials_file is None:
        parsed_args.credentials_file = Path(__file__).parent / "credentials.toml"

    if parsed_args.token_file is None:
        parsed_args.token_file = Path(__file__).parent / f"twitch_user_token.{parsed_args.environment}.json"

    return parsed_args



async def main() -> int:
    # make sure our output streams are properly encoded so that we can
    # not screw up Frédéric Chopin's name and such.
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding="utf-8", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding="utf-8", line_buffering=True)

    args = parse_args()

    logformat = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format=logformat)
    logging.getLogger("asyncio").setLevel(logging.DEBUG)

    if args.auth is not None:
        return await do_auth_flow(args, args.auth, logging.getLogger(f"auth.{args.auth}"))

    # Else, do a normal startup
    enabled_backends = [b for b in BACKEND_LIST if b not in args.disable_backend]

    logging.info("Ongwatch is in startup")
    logging.info(f"Enabled backends: {" ".join(enabled_backends)}")

    tasks: list[asyncio.Task] = []

    for backend in enabled_backends:
        logging.info(f"loading config for '{backend}.{args.environment}' from {args.credentials_file}")

        creds = get_credentials(args.credentials_file, backend, args.environment)
        module = importlib.import_module(f"_ongwatch.{backend}")
        logger = logging.getLogger(f"{backend}")
        if backend in args.debug_backend or "all" in args.debug_backend:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        tasks.append(asyncio.create_task(module.start(args, creds, logger)))

    # FIXME: what's the right way to exit cleanly(ish)?
    await asyncio.gather(*tasks)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
