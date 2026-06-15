import logging
from pathlib import Path
from typing import Any, cast

import toml

from .dispatcher import OnErrorPolicy, OutputConfig, QueueOverflowPolicy

COMMON_OUTPUT_CONFIG_KEYS = {
    "enabled",
    "on_error",
    "queue_max_size",
    "queue_overflow",
    "max_retries",
}


def get_config(cfgfile: Path) -> dict[str, Any]:
    """Load and return the full ongwatch.conf config as a dict."""
    return dict(toml.load(cfgfile))


def get_credentials(cfgfile: Path, subsystem: str, environment: str) -> dict[str, str] | None:
    config = toml.load(cfgfile)

    try:
        return cast(dict[str, str], config[environment][subsystem])
    except KeyError:
        logging.warning(f"no credentials found for '{environment}.{subsystem}'")
        return None


def as_config_section(value: Any, section_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Config section [{section_name}] must be a table")
    return value


def parse_int(
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


def parse_output_config(output_name: str, cfg: dict[str, Any]) -> OutputConfig:
    # parse_int already raises output-scoped messages for the numeric keys, so
    # evaluate those first and let them surface unwrapped. The enum/range rules
    # live in OutputConfig.__post_init__; we just prefix its error with the
    # output name.
    queue_max_size = parse_int(
        cfg.get("queue_max_size", 0), "queue_max_size", output_name, min_value=0
    )
    max_retries = parse_int(
        cfg.get("max_retries", 3), "max_retries", output_name, min_value=0
    )
    try:
        return OutputConfig(
            on_error=cfg.get("on_error", OnErrorPolicy.QUEUE),
            queue_max_size=queue_max_size,
            queue_overflow=cfg.get("queue_overflow", QueueOverflowPolicy.DROP_OLDEST),
            max_retries=max_retries,
        )
    except ValueError as exc:
        raise ValueError(f"Output '{output_name}' config: {exc}") from exc


def output_handler_config(cfg: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in cfg.items()
        if key not in COMMON_OUTPUT_CONFIG_KEYS
    }


# FIXME: can we simplify this?
def enabled_names(
    configured: dict[str, Any],
    enable_names: list[str],
    disable_names: list[str],
    section_name: str,
) -> list[str]:
    if enable_names and enable_names != ["all"]:
        selected = enable_names
    else:
        selected = []
        for name, cfg in configured.items():
            cfg_section = as_config_section(cfg, f"{section_name}.{name}")
            enabled = cfg_section.get("enabled", True)
            if not isinstance(enabled, bool):
                raise ValueError(
                    f"Config value '{section_name}.{name}.enabled' must be a boolean"
                )
            if enabled:
                selected.append(name)

    return [name for name in selected if name not in disable_names]
