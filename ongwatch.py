#!/usr/bin/env -S uv run --script --quiet
import argparse
import asyncio
import io
import logging
import platform
import signal
import sys
import time
from collections import deque
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

# ---------------------------------------------------------------------------
# Backend supervisor settings
# ---------------------------------------------------------------------------

# Sliding window for counting restarts.  If a backend fails _BACKEND_RESTART_MAX
# times within _BACKEND_RESTART_WINDOW seconds it is marked permanently failed.
_BACKEND_RESTART_WINDOW: float = 300.0   # seconds
_BACKEND_RESTART_MAX:    int   = 5       # restarts within the window
_BACKEND_BACKOFF_BASE:   float = 1.0     # initial backoff in seconds
_BACKEND_BACKOFF_MAX:    float = 60.0    # maximum backoff in seconds


async def _supervised_backend(
    name: str,
    startfunc: BackendStartHandler,
    args: argparse.Namespace,
    creds: dict[str, str] | None,
    logger: logging.Logger,
    dispatcher: Dispatcher,
) -> None:
    """
    Run a backend and automatically restart it on failure, with exponential
    backoff and a sliding-window restart budget.

    Returns normally when the restart budget is exhausted (permanent failure).
    Propagates CancelledError transparently so the main loop can cancel it on
    shutdown.
    """
    restart_times: deque[float] = deque()

    while True:
        try:
            await startfunc(args, creds, logger, dispatcher)
            # A clean return is unexpected for long-running backends.
            logger.warning("Backend '%s' exited cleanly; scheduling restart", name)
        except asyncio.CancelledError:
            raise   # propagate shutdown — do not restart
        except Exception:
            logger.error("Backend '%s' failed with unhandled exception", name, exc_info=True)

        # Prune timestamps that have aged out of the window.
        now = time.monotonic()
        cutoff = now - _BACKEND_RESTART_WINDOW
        while restart_times and restart_times[0] < cutoff:
            restart_times.popleft()

        if len(restart_times) >= _BACKEND_RESTART_MAX:
            logger.error(
                "Backend '%s' has failed %d times in %.0fs; "
                "marking it permanently failed",
                name, _BACKEND_RESTART_MAX, _BACKEND_RESTART_WINDOW,
            )
            return  # the main loop will notice and eventually shut down

        attempt = len(restart_times) + 1
        backoff = min(_BACKEND_BACKOFF_BASE * (2 ** len(restart_times)), _BACKEND_BACKOFF_MAX)
        restart_times.append(now)

        logger.warning(
            "Restarting backend '%s' (attempt %d of %d) in %.1fs",
            name, attempt, _BACKEND_RESTART_MAX, backoff,
        )
        try:
            await asyncio.sleep(backoff)
        except asyncio.CancelledError:
            raise   # shutdown during backoff — propagate


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
    config_file: Path,
    enable_output: list[str],
    disable_output: list[str],
    debug_output: list[str],
) -> tuple[list[tuple[str, Any, OutputConfig]], list[Any]]:
    """
    Parse [outputs.*.<environment>] sections from ongwatch.conf, instantiate
    each output, and return two parallel lists:
      - triples suitable for Dispatcher.__init__
      - the raw output instances (for calling stop() at shutdown)
    """
    outputs_cfg: dict[str, Any] = config.get(environment, {}).get("outputs", {})

    if enable_output and enable_output != ["all"]:
        enabled_outputs = enable_output
    else:
        enabled_outputs = [
            name for name, cfg in outputs_cfg.items()
            if cfg.get("enabled", True)
        ]
    enabled_outputs = [o for o in enabled_outputs if o not in disable_output]

    triples: list[tuple[str, Any, OutputConfig]] = []
    instances: list[Any] = []

    for output_name in enabled_outputs:
        env_cfg: dict[str, Any] = outputs_cfg.get(output_name, {})

        logging.info(
            f"loading config for '{environment}.{output_name}' from {config_file}")
        try:
            module = get_output(output_name)
            output = module.create(env_cfg)
        except Exception:
            logging.exception(f"failed to load output '{output_name}'; skipping")
            continue

        logger = logging.getLogger(output_name)
        if output_name in debug_output or "all" in debug_output:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

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
    # Load ongwatch.conf
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
    output_triples, output_instances = _load_outputs(
        config, args.environment, args.config_file,
        args.enable_output, args.disable_output, args.debug_output,
    )

    for output in output_instances:
        await output.start()

    dispatcher = Dispatcher(output_triples, heartbeat_interval=heartbeat_interval)
    await dispatcher.start()

    # ------------------------------------------------------------------
    # Start backends
    # ------------------------------------------------------------------
    if args.enable_backend and args.enable_backend != ["all"]:
        # CLI --enable-backend takes full precedence
        enabled_backends = args.enable_backend
    else:
        backends_cfg: dict[str, Any] = config.get(args.environment, {}).get("backends", {})
        if not backends_cfg:
            logging.error(
                f"No [{args.environment}.backends.*] sections found in {args.config_file}; "
                f"add at least one [{args.environment}.backends.<name>] section"
            )
            return 1

        enabled_backends = [
            name for name, cfg in backends_cfg.items()
            if cfg.get("enabled", True)
        ]

    enabled_backends = [b for b in enabled_backends if b not in args.disable_backend]

    if not enabled_backends:
        logging.error(
            f"No backends enabled for environment '{args.environment}'; "
            "check [backends.*] sections in ongwatch.conf"
        )
        return 1

    logging.info("Ongwatch is in startup")
    logging.info(f"Enabled backends: {' '.join(enabled_backends)}")

    supervised_tasks: list[asyncio.Task[None]] = []

    for backend in enabled_backends:
        logging.info(
            f"loading config for '{args.environment}.{backend}' from {args.config_file}")
        logging.info(
            f"loading credentials for '{args.environment}.{backend}' from {args.credentials_file}")

        creds = get_credentials(args.credentials_file, backend, args.environment)
        module = backends.get_backend(backend)
        logger = logging.getLogger(f"{backend}")
        if backend in args.debug_backend or "all" in args.debug_backend:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        startfunc: BackendStartHandler = module.start
        supervised_tasks.append(
            asyncio.create_task(
                _supervised_backend(backend, startfunc, args, creds, logger, dispatcher),
                name=f"supervisor:{backend}",
            )
        )

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
        # SelectorEventLoop on Windows never calls signal.set_wakeup_fd(), so
        # SIGINT won't interrupt select() — the loop can block for up to the
        # heartbeat interval before noticing Ctrl+C.  Wire up the loop's own
        # self-pipe as the wakeup fd so signals wake select() immediately.
        if hasattr(loop, '_csock'):
            signal.set_wakeup_fd(loop._csock.fileno())

    try:
        # Supervisor tasks return normally only on permanent failure; they
        # propagate CancelledError on shutdown.  Keep looping until a shutdown
        # signal arrives or every backend has permanently failed.
        alive = list(supervised_tasks)
        while alive:
            done, _ = await asyncio.wait(
                [shutdown_task, *alive],
                return_when=asyncio.FIRST_COMPLETED,
            )
            if shutdown_task in done:
                break
            alive = [t for t in alive if not t.done()]
            if not alive:
                logging.error(
                    "All backends have permanently failed; initiating shutdown"
                )
    finally:
        logging.info("Shutting down...")

        # 1. Stop backends — no new events after this point
        shutdown_task.cancel()
        for task in supervised_tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(shutdown_task, *supervised_tasks, return_exceptions=True)

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
        help="file with credentials (credentials.conf)"
    )

    parser.add_argument(
        "--config-file",
        type=Path,
        default=None,
        help="runtime config file (ongwatch.conf)"
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

    parser.add_argument(
        "--debug-output",
        type=str,
        action="append",
        default=[],
        help="enable debug logging for named output"
    )

    parser.add_argument(
        "--enable-output",
        type=str,
        action="append",
        default=[],
        help="enable named output"
    )

    parser.add_argument(
        "--disable-output",
        type=str,
        action="append",
        default=[],
        help="disable named output"
    )

    parsed_args = parser.parse_args()

    if parsed_args.credentials_file is None:
        parsed_args.credentials_file = Path(__file__).parent / "credentials.conf"

    if parsed_args.config_file is None:
        parsed_args.config_file = Path(__file__).parent / "ongwatch.conf"

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
