#!/usr/bin/env -S uv run --script --quiet
import argparse
import asyncio
import io
import logging
import os
import platform
import signal
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import _ongwatch.backends as backends
from _ongwatch.backends import BackendAuthHandler, BackendStartHandler
from _ongwatch.dispatcher import (Dispatcher, OnErrorPolicy, OutputConfig,
                                  QueueOverflowPolicy)
from _ongwatch.outputs import get_output
from _ongwatch.util import get_credentials

import toml
from tdvutil import ppretty
from tdvutil.argparse import CheckFile

os.environ["PYTHON_COLORS"] = "0"
os.environ["PYTHONNODEBUGRANGES"] = "1"


# Sliding window for counting restarts.  If a backend fails _BACKEND_RESTART_MAX
# times within _BACKEND_RESTART_WINDOW seconds it is marked permanently failed.
_BACKEND_RESTART_WINDOW: float = 300.0   # seconds
_BACKEND_RESTART_MAX:    int   = 5       # restarts within the window
_BACKEND_BACKOFF_BASE:   float = 1.0     # initial backoff in seconds
_BACKEND_BACKOFF_MAX:    float = 60.0    # maximum backoff in seconds

_COMMON_OUTPUT_CONFIG_KEYS = {
    "enabled",
    "on_error",
    "queue_max_size",
    "queue_overflow",
    "circuit_break_cooldown",
    "circuit_break_flush_queue",
    "max_retries",
}

@dataclass
class BackendSpec:
    name: str
    startfunc: BackendStartHandler
    creds: dict[str, str] | None
    logger: logging.Logger

# Run a backend and automatically restart it on failure, with exponential
# backoff and a sliding-window restart budget.
#
# Returns normally when the restart budget is exhausted (permanent failure).
# Propagates CancelledError transparently so the main loop can cancel it on
# shutdown.
async def _supervised_backend(
    name: str,
    startfunc: BackendStartHandler,
    args: argparse.Namespace,
    creds: dict[str, str] | None,
    logger: logging.Logger,
    dispatcher: Dispatcher,
) -> None:
    restart_times: deque[float] = deque()

    while True:
        try:
            await startfunc(args, creds, logger, dispatcher)
            # A clean return is unexpected for long-running backends.
            logger.warning("Backend '%s' exited cleanly; scheduling restart", name)
        except asyncio.CancelledError:
            # propagate shutdown — do not restart
            raise
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
            return

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
            # shutdown during backoff
            raise


async def do_auth_flow(args: argparse.Namespace, backend: str, logger: logging.Logger) -> int:
    logger.setLevel(logging.WARNING)  # quiet things down
    creds = get_credentials(args.credentials_file, backend, args.environment)

    # FIXME: make it possible to have a backend with no auth info (maybe)
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


def _as_config_section(value: Any, section_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Config section [{section_name}] must be a table")
    return value


def _parse_bool(value: Any, key: str, output_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ValueError(f"Output '{output_name}' config value '{key}' must be a boolean")


def _parse_int(
    value: Any,
    key: str,
    output_name: str,
    *,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    if isinstance(value, bool):
        raise ValueError(f"Output '{output_name}' config value '{key}' must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Output '{output_name}' config value '{key}' must be an integer"
        ) from exc
    if min_value is not None and parsed < min_value:
        raise ValueError(
            f"Output '{output_name}' config value '{key}' must be >= {min_value}"
        )
    if max_value is not None and parsed > max_value:
        raise ValueError(
            f"Output '{output_name}' config value '{key}' must be <= {max_value}"
        )
    return parsed


def _parse_float(
    value: Any,
    key: str,
    output_name: str,
    *,
    min_value: float | None = None,
) -> float:
    if isinstance(value, bool):
        raise ValueError(f"Output '{output_name}' config value '{key}' must be a number")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Output '{output_name}' config value '{key}' must be a number"
        ) from exc
    if min_value is not None and parsed < min_value:
        raise ValueError(
            f"Output '{output_name}' config value '{key}' must be >= {min_value}"
        )
    return parsed


def _parse_output_config(output_name: str, cfg: dict[str, Any]) -> OutputConfig:
    on_error_raw = cfg.get("on_error", OnErrorPolicy.QUEUE)
    try:
        on_error = OnErrorPolicy(on_error_raw)
    except ValueError as exc:
        raise ValueError(
            f"Output '{output_name}' config value 'on_error' must be 'queue' or 'drop'"
        ) from exc

    queue_overflow_raw = cfg.get("queue_overflow", QueueOverflowPolicy.DROP_OLDEST)
    try:
        queue_overflow = QueueOverflowPolicy(queue_overflow_raw)
    except ValueError as exc:
        raise ValueError(
            "Output "
            f"'{output_name}' config value 'queue_overflow' must be "
            "'drop_oldest', 'drop_newest', or 'circuit_break'"
        ) from exc

    output_config = OutputConfig(
        on_error=on_error,
        queue_max_size=_parse_int(
            cfg.get("queue_max_size", 0), "queue_max_size", output_name, min_value=0
        ),
        queue_overflow=queue_overflow,
        circuit_break_cooldown=_parse_float(
            cfg.get("circuit_break_cooldown", 300.0),
            "circuit_break_cooldown",
            output_name,
            min_value=0.0,
        ),
        circuit_break_flush_queue=_parse_bool(
            cfg.get("circuit_break_flush_queue", False),
            "circuit_break_flush_queue",
            output_name,
        ),
        max_retries=_parse_int(
            cfg.get("max_retries", 3), "max_retries", output_name, min_value=0
        ),
    )

    return output_config


def _output_handler_config(cfg: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in cfg.items()
        if key not in _COMMON_OUTPUT_CONFIG_KEYS
    }


def _enabled_names(
    configured: dict[str, Any],
    enable_names: list[str],
    disable_names: list[str],
    section_name: str,
) -> list[str]:
    if enable_names and enable_names != ["all"]:
        enabled_names = enable_names
    else:
        enabled_names = []
        for name, cfg in configured.items():
            cfg_section = _as_config_section(cfg, f"{section_name}.{name}")
            enabled = cfg_section.get("enabled", True)
            if not isinstance(enabled, bool):
                raise ValueError(
                    f"Config value '{section_name}.{name}.enabled' must be a boolean"
                )
            if enabled:
                enabled_names.append(name)

    return [name for name in enabled_names if name not in disable_names]


def _load_backend_specs(
    config: dict[str, Any],
    args: argparse.Namespace,
) -> list[BackendSpec]:
    environment_cfg = _as_config_section(config.get(args.environment, {}), args.environment)
    backends_cfg = _as_config_section(
        environment_cfg.get("backends", {}),
        f"{args.environment}.backends",
    )

    if not backends_cfg and not args.enable_backend:
        raise ValueError(
            f"No [{args.environment}.backends.*] sections found in {args.config_file}; "
            f"add at least one [{args.environment}.backends.<name>] section"
        )

    enabled_backends = _enabled_names(
        backends_cfg,
        args.enable_backend,
        args.disable_backend,
        f"{args.environment}.backends",
    )

    if not enabled_backends:
        raise ValueError(
            f"No backends enabled for environment '{args.environment}'; "
            "check [backends.*] sections in ongwatch.conf"
        )

    specs: list[BackendSpec] = []
    for backend in enabled_backends:
        logging.info(
            f"loading config for '{args.environment}.{backend}' from {args.config_file}")
        logging.info(
            f"loading credentials for '{args.environment}.{backend}' from {args.credentials_file}")

        creds = get_credentials(args.credentials_file, backend, args.environment)
        try:
            module = backends.get_backend(backend)
        except ModuleNotFoundError as exc:
            raise ValueError(f"No such backend '{backend}': {exc}") from exc

        if "start" not in dir(module):
            raise ValueError(f"No start handler available for backend '{backend}'")

        logger = logging.getLogger(f"{backend}")
        if backend in args.debug_backend or "all" in args.debug_backend:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        specs.append(BackendSpec(
            name=backend,
            startfunc=module.start,
            creds=creds,
            logger=logger,
        ))

    return specs


# Get output configs from config file, instantiate  each output, and return
# two lists: one for the dispatcher with (name, instance, config) tuples,
# and one with the raw output instances (for calling stop() at shutdown).
#
# FIXME: Look at how we use/store these, wee if we really need two returns
def _load_outputs(
    config: dict[str, Any],
    environment: str,
    config_file: Path,
    enable_output: list[str],
    disable_output: list[str],
    debug_output: list[str],
) -> tuple[list[tuple[str, Any, OutputConfig]], list[Any]]:
    environment_cfg = _as_config_section(config.get(environment, {}), environment)
    outputs_cfg = _as_config_section(
        environment_cfg.get("outputs", {}),
        f"{environment}.outputs",
    )
    enabled_outputs = _enabled_names(
        outputs_cfg,
        enable_output,
        disable_output,
        f"{environment}.outputs",
    )

    triples: list[tuple[str, Any, OutputConfig]] = []
    instances: list[Any] = []

    for output_name in enabled_outputs:
        env_cfg = _as_config_section(
            outputs_cfg.get(output_name, {}),
            f"{environment}.outputs.{output_name}",
        )
        output_config = _parse_output_config(output_name, env_cfg)

        logging.info(
            f"loading config for '{environment}.{output_name}' from {config_file}")
        try:
            module = get_output(output_name)
            handler_cfg = _output_handler_config(env_cfg)
            if "validate_config" in dir(module):
                module.validate_config(handler_cfg)
            output = module.create(env_cfg)
        except Exception as exc:
            raise ValueError(f"failed to load output '{output_name}': {exc}") from exc

        logger = logging.getLogger(output_name)
        if output_name in debug_output or "all" in debug_output:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        name = f"{output_name}.{environment}"
        triples.append((name, output, output_config))
        instances.append(output)

    return triples, instances


# FIXME: A bit long, might need refactoring
async def async_main(args: argparse.Namespace) -> int:
    config: dict[str, Any] = {}
    if args.config_file.exists():
        config = dict(toml.load(args.config_file))
    else:
        # FIXME: Should this be an error?
        logging.warning(f"Config file {args.config_file} not found; no outputs will be active")

    logging.info("Ongwatch is in startup")

    try:
        dispatcher_section = _as_config_section(config.get("dispatcher", {}), "dispatcher")
        heartbeat_interval = _parse_float(
            dispatcher_section.get("heartbeat_interval", 60),
            "heartbeat_interval",
            "dispatcher",
            min_value=0.001,
        )

        output_triples, output_instances = _load_outputs(
            config, args.environment, args.config_file,
            args.enable_output, args.disable_output, args.debug_output,
        )
        backend_specs = _load_backend_specs(config, args)
    except ValueError as exc:
        logging.error(str(exc))
        return 1

    logging.info(f"Enabled backends: {' '.join(spec.name for spec in backend_specs)}")

    # FIXME: We should probably configure loggers to pass to outputs, like we
    # do for backends
    dispatcher = Dispatcher(output_triples, heartbeat_interval=heartbeat_interval)
    dispatcher_started = False
    started_outputs: list[Any] = []
    supervised_tasks: list[asyncio.Task[None]] = []
    shutdown_task: asyncio.Task[bool] | None = None
    exit_code = 0

    try:
        for output in output_instances:
            await output.start()
            started_outputs.append(output)

        await dispatcher.start()
        dispatcher_started = True

        for spec in backend_specs:
            supervised_tasks.append(
                asyncio.create_task(
                    _supervised_backend(
                        spec.name,
                        spec.startfunc,
                        args,
                        spec.creds,
                        spec.logger,
                        dispatcher,
                    ),
                    name=f"supervisor:{spec.name}",
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

        # Supervisor tasks return normally only on permanent failure; they
        # propagate CancelledError on shutdown.  Keep looping until a shutdown
        # signal arrives or every backend has permanently failed.
        alive = list(supervised_tasks)
        while alive:
            assert shutdown_task is not None
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
                exit_code = 1
    except Exception:
        logging.exception("Ongwatch failed during startup/runtime")
        exit_code = 1
    finally:
        logging.info("Shutting down...")

        # Stop backends — no new events after this point
        if shutdown_task is not None:
            shutdown_task.cancel()
        for task in supervised_tasks:
            if not task.done():
                task.cancel()
        shutdown_items: list[asyncio.Task[Any]] = list(supervised_tasks)
        if shutdown_task is not None:
            shutdown_items.append(shutdown_task)
        if shutdown_items:
            await asyncio.gather(*shutdown_items, return_exceptions=True)

        # Drain queues for up to 30 seconds
        if dispatcher_started:
            await dispatcher.drain(timeout=30)

        # Cancel dispatcher internal tasks
        await dispatcher.stop()

        # Close each output
        for output in reversed(started_outputs):
            try:
                await output.stop()
            except Exception:
                logging.exception("Output failed during stop")

    return exit_code


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

    # If we're being asked to auth, only do that
    if args.auth is not None:
        return asyncio.run(do_auth_flow(args, args.auth, logging.getLogger(f"auth.{args.auth}")), debug=args.debug_asyncio)

    # else, run the main loop
    return asyncio.run(async_main(args), debug=args.debug_asyncio)


if __name__ == "__main__":
    sys.exit(main())
