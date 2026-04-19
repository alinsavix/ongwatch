import datetime
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, cast

import aiohttp
import pytz
import toml
from tdvutil import ppretty


def out(msg: str) -> None:
    """Log a message to stderr (log-to-stderr utility; stdout is owned by outputs)."""
    log(msg)


def log(msg: str) -> None:
    print(timestr_est(now()), msg, file=sys.stderr)
    sys.stderr.flush()


def now() -> int:
    return int(time.time())


def timestr_est(ts: int) -> str:
    utc_time = datetime.datetime.fromtimestamp(ts, datetime.UTC)
    eastern_zone = pytz.timezone('US/Eastern')
    eastern_time = utc_time.replace(tzinfo=pytz.utc).astimezone(eastern_zone)
    return eastern_time.strftime("%Y-%m-%d %H:%M:%S")


def get_token(token_file: Path) -> Dict[str, str]:
    with open(token_file, 'r') as f:
        return cast(Dict[str, str], json.load(f))


async def get_json_url(url: str) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status} for {url}")

            # else
            return await response.json()


def get_credentials(cfgfile: Path, subsystem: str, environment: str) -> Dict[str, str] | None:
    config = toml.load(cfgfile)

    try:
        return config[subsystem][environment]
    except KeyError:
        logging.warning(f"no credentials found for '{subsystem}.{environment}'")
        return None


def get_config(cfgfile: Path) -> Dict[str, Any]:
    """Load and return the full ongwatch.toml config as a dict."""
    return dict(toml.load(cfgfile))
