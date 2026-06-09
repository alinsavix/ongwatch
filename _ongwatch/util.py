import datetime
import sys
import time
from typing import Any, Dict, cast

import aiohttp
import pytz
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


async def get_json_url(url: str) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session, session.get(url) as response:
        if response.status != 200:
            raise Exception(f"HTTP {response.status} for {url}")

        # else
        return cast(Dict[str, Any], await response.json())
