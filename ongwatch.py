#!/usr/bin/env -S uv run --script --quiet
import argparse
import asyncio
import io
import logging
import platform
import signal
import sys
from pathlib import Path
from typing import Any, cast

import _ongwatch.backends as backends
from _ongwatch.backends import BackendAuthHandler, BackendStartHandler
from _ongwatch.dispatcher import Dispatcher, OutputConfig
from _ongwatch.outputs import get_output
from _ongwatch.util import get_credentials

import toml
from tdvutil import ppretty
from tdvutil.argparse import CheckFile


async def do_auth_flow(args: argparse.Namespace, backend: str, logger: logging.Logger) -> int:
    logger.setLevel(logging.WARNING)  # quiet things down
    creds = get_credentials(args.credentials_file, backend, args.environment)
    if creds is None:
        logger.error(f"No credentials found for {backend}")
        return 1

    try:
        module = backends.get_backend(f"auth.{backend}")
    except ModuleNotFoundError as e:
        logger.error(f"No such backend '{backend}': {e}")
        return 1

    if "auth" not in dir(module):
        logger.error(f"No auth handler available for Backend '{backend}'")
        return 1

    authfunc: BackendAuthHandler = module.auth
    return 0 if await authfunc(args, creds, logging.getLogger(args.auth)) else 1


def _load_outputs(
    config: dict[str, Any],
    environment: str,
) -> tuple[list[tuple[str, Any, OutputConfig]], list[Any]]:
    """
    Parse [outputs.*.<environment>] sections from ongwatch.toml, instantiate
    each output, and return two parallel lists:
      - triples suitable for Dispatcher.__init__
      - the raw output instances (for calling stop() at shutdown)
    """
    triples: list[tuple[str, Any, OutputConfig]] = []
    instances: list[Any] = []

    for output_name, env_map in config.get("outputs", {}).items():
        if environment not in env_map:
            continue
        env_cfg: dict[str, Any] = env_map[environment]

        module = get_output(output_name)
        output = module.create(env_cfg)

        output_config = OutputConfig(
            on_error=env_cfg.get("on_error", "queue"),
            queue_max_size=int(env_cfg.get("queue_max_size", 0)),
            queue_overflow=env_cfg.get("queue_overflow", "drop_oldest"),
            circuit_break_cooldown=float(env_cfg.get("circuit_break_cooldown", 300.0)),
            circuit_break_flush_queue=bool(env_cfg.get("circuit_break_flush_queue", False)),
            max_retries=int(env_cfg.get("max_retries", 3)),
        )

        name = f"{output_name}.{environment}"
        triples.append((name, output, output_config))
        instances.append(output)

    return triples, instances


async def async_main(args: argparse.Namespace) -> int:
    # ------------------------------------------------------------------
    # Load ongwatch.toml
    # ------------------------------------------------------------------
    config: dict[str, Any] = {}
    if args.config_file.exists():
        config = dict(toml.load(args.config_file))
    else:
        logging.warning(f"Config file {args.config_file} not found; no outputs will be active")

    dispatcher_section: dict[str, Any] = config.get("dispatcher", {})
    heartbeat_interval = float(dispatcher_section.get("heartbeat_interval", 60))

    # ------------------------------------------------------------------
    # Start outputs and build dispatcher
    # ------------------------------------------------------------------
    output_triples, output_instances = _load_outputs(config, args.environment)

    for output in output_instances:
        await output.start()

    dispatcher = Dispatcher(output_triples, heartbeat_interval=heartbeat_interval)
    await dispatcher.start()

    # ------------------------------------------------------------------
    # Start backends
    # ------------------------------------------------------------------
    if not args.enable_backend or args.enable_backend == ["all"]:
        enabled_backends = backends.backend_list()
    else:
        enabled_backends = args.enable_backend

    enabled_backends = [b for b in enabled_backends if b not in args.disable_backend]

    logging.info("Ongwatch is in startup")
    logging.info(f"Enabled backends: {' '.join(enabled_backends)}")

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
        tasks.append(asyncio.create_task(startfunc(args, creds, logger, dispatcher)))

    shutdown_event = asyncio.Event()
    shutdown_task = asyncio.create_task(shutdown_event.wait())

    # Setup Windows-compatible keyboard interrupt handler
    def handle_interrupt() -> None:
        loop.call_soon_threadsafe(shutdown_event.set)

    loop = asyncio.get_running_loop()
    if platform.system() != "Windows":
        loop.add_signal_handler(signal.SIGINT, handle_interrupt)
        loop.add_signal_handler(signal.SIGTERM, handle_interrupt)
    else:
        # Windows doesn't support loop.add_signal_handler
        signal.signal(signal.SIGINT, lambda signum, frame: handle_interrupt())
        signal.signal(signal.SIGTERM, lambda signum, frame: handle_interrupt())

    try:
        done, pending = await asyncio.wait(
            [shutdown_task, *tasks],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in done:
            if task is not shutdown_task and not task.cancelled():
                if exc := task.exception():
                    logging.error("Backend task failed", exc_info=exc)
    finally:
        logging.info("Shutting down...")

        # 1. Stop backends — no new events after this point
        shutdown_task.cancel()
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(shutdown_task, *tasks, return_exceptions=True)

        # 2. Drain queues (up to 30 s)
        await dispatcher.drain(timeout=30)

        # 3. Cancel dispatcher internal tasks
        await dispatcher.stop()

        # 4. Close each output
        for output in output_instances:
            await output.stop()

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Share to discord some of the stream things that have happened")

    parser.add_argument(
        "--credentials-file", "-c",
        type=Path,
        default=None,
        action=CheckFile(must_exist=True),
        help="file with credentials (credentials.toml)"
    )

    parser.add_argument(
        "--config-file",
        type=Path,
        default=None,
        help="runtime config file (ongwatch.toml)"
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

    if parsed_args.config_file is None:
        parsed_args.config_file = Path(__file__).parent / "ongwatch.toml"

    if parsed_args.token_file is None:
        parsed_args.token_file = Path(__file__).parent / f"twitch_user_token.{parsed_args.environment}.json"

    return parsed_args


def main() -> int:
    # make sure our output streams are properly encoded so that we can
    # not screw up Frédéric Chopin's name and such.
    #
    # FIXME: the typing on this is kinda ugly, see if we can figure out better
    sys.stdout = io.TextIOWrapper(cast(io.TextIOBase, sys.stdout).detach(), encoding="utf-8", line_buffering=True)
    sys.stderr = io.TextIOWrapper(cast(io.TextIOBase, sys.stderr).detach(), encoding="utf-8", line_buffering=True)

    # paho-mqtt (used by aiomqtt) requires add_reader/add_writer, which are
    # only available on SelectorEventLoop — not the Windows default ProactorEventLoop.
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    args = parse_args()

    logformat = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format=logformat)

    if args.auth is not None:
        return asyncio.run(do_auth_flow(args, args.auth, logging.getLogger(f"auth.{args.auth}")), debug=args.debug_asyncio)

    # else, run the main loop
    return asyncio.run(async_main(args), debug=args.debug_asyncio)


if __name__ == "__main__":
    sys.exit(main())
