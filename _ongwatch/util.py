import datetime
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict

import aiohttp
import pytz
import toml
from tdvutil import ppretty
from tdvutil.argparse import CheckFile


# FIXME: use real logging ffs
def out(msg: str) -> None:
    print(timestr_est(now()), msg, file=sys.stdout)
    sys.stdout.flush()

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


def printsupport(ts: int, gifter: str = "", supporter: str = "", type: str = "",
                 amount: float = 0.0, comment: str = ""):
    ts_str = timestr_est(ts)
    outstr = f"{ts_str}\t\t{gifter}\t{supporter}\t{type}\t${amount:0.2f}\tna\t{comment}"
    print(outstr, file=sys.stdout)
    sys.stdout.flush()

    # FIXME: super sloppy
    print(outstr, file=sys.stderr)
    sys.stderr.flush()


def printextra(ts: int, message: str):
    message = message.strip()
    print("  " + message + "\n", file=sys.stdout)
    sys.stdout.flush()

    # FIXME: super sloppy
    print("  " + message + "\n", file=sys.stderr)
    sys.stderr.flush()


async def get_json_url(url) -> Dict[str, Any]:
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
        logging.error(f"no config found for '{subsystem}.{environment}'")
        return None
