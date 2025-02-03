#!/usr/bin/env python
import argparse
import asyncio
import datetime
import importlib
import io
import json
# from loguru import logger
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Text

import pytz
import toml
from tdvutil import ppretty
from tdvutil.argparse import CheckFile

import _ongwatch.streamelements as streamelements
import _ongwatch.streamlabs as streamlabs
import _ongwatch.twitch as twitch
from _ongwatch.util import log

# FIXME: generate this dynamically?
BACKEND_LIST = ["twitch", "streamelements", "streamlabs"]


def get_credentials(cfgfile: Path, subsystem: str, environment: str) -> Dict[str, str]|None:
    log(f"loading config from {cfgfile}")
    config = toml.load(cfgfile)

    try:
        return config[subsystem][environment]
    except KeyError:
        return None


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
        parsed_args.token_file = Path(__file__).parent / "user_token.json"

    print(f"parsed_args.debug_backend: {parsed_args.debug_backend}")

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

    enabled_backends = [b for b in BACKEND_LIST if b not in args.disable_backend]

    logging.info("Ongwatch is in startup")
    logging.info(f"Enabled backends: {" ".join(enabled_backends)}")


    tasks: list[asyncio.Task] = []

    for backend in enabled_backends:
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
