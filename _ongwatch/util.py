import datetime
import sys
import time
from pathlib import Path
from typing import Any, Dict

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
