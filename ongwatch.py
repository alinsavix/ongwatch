#!/usr/bin/env python
import argparse
import asyncio
import importlib
import io
import logging
import platform
import signal
import sys
from pathlib import Path
from typing import (Any, Awaitable, Callable, Coroutine, Dict, Optional, Text,
                    cast)

from tdvutil import ppretty
from tdvutil.argparse import CheckFile

import _ongwatch.backends as backends
from _ongwatch.util import get_credentials

# FIXME: generate this dynamically?
BACKEND_LIST = ["twitch", "streamelements", "streamlabs"]

# FIXME: define these in a backend module or similar
BackendAuthHandler = Callable[[argparse.Namespace, Dict[str, str] | None, logging.Logger], Coroutine[None, None, bool]]
BackendStartHandler = Callable[[argparse.Namespace, Dict[str, str] | None, logging.Logger], Coroutine[None, None, None]]

async def do_auth_flow(args: argparse.Namespace, backend: str, logger: logging.Logger) -> int:
    logger.setLevel(logging.WARNING)  # quiet things down
    creds = get_credentials(args.credentials_file, backend, args.environment)
    if creds is None:
        logger.error(f"No credentials found for {backend}")
        return False

    try:
        module = backends.get_backend(f"auth.{backend}")
    except ModuleNotFoundError as e:
        logger.error(f"No such backend '{backend}': {e}")
        return False

    if "auth" not in dir(module):
        logger.error(f"No auth handler available for Backend '{backend}'")
        return False

    authfunc: BackendAuthHandler = module.auth
    return await authfunc(args, creds, logging.getLogger(args.auth))


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

    parser.add_argument(
        "--debug-asyncio",
        action="store_true",
        default=False,
        help="enable debugging of asyncio"
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
        "--enable-backend",
        type=str,
        action="append",
        default=[],
        help="enable named backend"
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


async def async_main(args: argparse.Namespace) -> int:
    if not args.enable_backend or args.enable_backend == ["all"]:
        enabled_backends = backends.backend_list()
    else:
        enabled_backends = args.enable_backend

    enabled_backends = [b for b in enabled_backends if b not in args.disable_backend]

    logging.info("Ongwatch is in startup")
    logging.info(f"Enabled backends: {" ".join(enabled_backends)}")

    tasks: list[asyncio.Task[None]] = []

    for backend in enabled_backends:
        logging.info(
            f"loading config for '{backend}.{args.environment}' from {args.credentials_file}")

        creds = get_credentials(args.credentials_file, backend, args.environment)
        module = backends.get_backend(backend)
        logger = logging.getLogger(f"{backend}")
        if backend in args.debug_backend or "all" in args.debug_backend:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        startfunc: BackendStartHandler = module.start
        tasks.append(asyncio.create_task(startfunc(args, creds, logger)))

    shutdown_event = asyncio.Event()
    shutdown_task = asyncio.create_task(shutdown_event.wait())

    # Setup Windows-compatible keyboard interrupt handler
    def handle_interrupt():
        asyncio.get_event_loop().call_soon_threadsafe(shutdown_event.set)

    loop = asyncio.get_event_loop()
    if platform.system() != "Windows":
        loop.add_signal_handler(signal.SIGINT, handle_interrupt)
        loop.add_signal_handler(signal.SIGTERM, handle_interrupt)
    else:
        # Windows doesn't support loop.add_signal_handler
        signal.signal(signal.SIGINT, lambda signum, frame: handle_interrupt())
        signal.signal(signal.SIGTERM, lambda signum, frame: handle_interrupt())

    # from tdvutil import alintrospect
    # alintrospect(waits)
    # alintrospect(tasks[0])

    try:
        # await asyncio.wait()
        done, pending = await asyncio.wait(
            [shutdown_task, *tasks],
            return_when=asyncio.FIRST_COMPLETED
            )
    finally:
        logging.info("Shutting down...")
        # Cancel all running tasks
        for task in tasks:
            if not task.done():
                task.cancel()
        # Wait for all tasks to be cancelled
        await asyncio.gather(*tasks, return_exceptions=True)

    return 0


def main() -> int:
    # make sure our output streams are properly encoded so that we can
    # not screw up Frédéric Chopin's name and such.
    #
    # FIXME: the typing on this is kinda ugly, see if we can figure out better
    sys.stdout = io.TextIOWrapper(cast(io.TextIOBase, sys.stdout).detach(), encoding="utf-8", line_buffering=True)
    sys.stderr = io.TextIOWrapper(cast(io.TextIOBase, sys.stderr).detach(), encoding="utf-8", line_buffering=True)

    args = parse_args()

    logformat = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format=logformat)

    # FIXME: is this the same as calling asyncio.run() with debug=True?
    # logging.getLogger("asyncio").setLevel(logging.DEBUG)

    if args.auth is not None:
        return asyncio.run(do_auth_flow(args, args.auth, logging.getLogger(f"auth.{args.auth}")), debug=args.debug_asyncio)

    # else, run the main loop
    return asyncio.run(async_main(args), debug=args.debug_asyncio)


if __name__ == "__main__":
    # sys.exit(asyncio.run(main(), debug=True))
    sys.exit(main())
