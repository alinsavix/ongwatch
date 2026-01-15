"""
Bumplog output handler - replicates current stdout/stderr tab-separated output.

This handler duplicates the existing printsupport/out/printextra functionality,
writing tab-separated event data to stdout and stderr for backwards compatibility.
"""

import argparse
import asyncio
import logging
import sys
from typing import Dict, Optional

from _ongwatch.event import Event, EventType
from _ongwatch.util import timestr_est


async def start(
    args: argparse.Namespace,
    creds: Optional[Dict[str, str]],
    logger: logging.Logger,
    event_queue: asyncio.Queue[Event]
) -> None:
    """
    Start the bumplog output handler.

    This handler processes events from the queue and outputs them in the
    traditional tab-separated format to stdout and stderr.
    """
    logger.info("Bumplog output handler starting")

    # No initialization needed for bumplog (no external resources)

    try:
        while True:
            try:
                # Get event from queue
                event = await event_queue.get()

                # Process event based on type
                await process_event(event, logger)

                # Mark task done
                event_queue.task_done()

            except asyncio.CancelledError:
                logger.info("Shutdown signal received")
                raise

            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)
                event_queue.task_done()

    except asyncio.CancelledError:
        logger.info("Bumplog output handler shutting down")
        sys.stdout.flush()
        sys.stderr.flush()
        raise


async def process_event(event: Event, logger: logging.Logger) -> None:
    """Process a single event and output to stdout/stderr"""

    # Handle support events (monetary)
    if event.event_type in [
        EventType.SUBSCRIPTION,
        EventType.SUBSCRIPTION_GIFT,
        EventType.BITS,
        EventType.TIP,
        EventType.RAID,
        EventType.RAFFLE
    ]:
        output_support_event(event)

    # Handle song requests
    elif event.event_type == EventType.SONG_REQUEST:
        output_extra_event(event)

    # Handle stream state changes
    elif event.event_type in [
        EventType.STREAM_ONLINE,
        EventType.STREAM_OFFLINE,
        EventType.HYPE_TRAIN_BEGIN,
        EventType.HYPE_TRAIN_END
    ]:
        output_state_event(event)

    else:
        logger.warning(f"Unknown event type: {event.event_type}")


def output_support_event(event: Event) -> None:
    """
    Output support event in tab-separated format (replicates printsupport).

    Format: timestamp\t\tgifter\tsupporter\ttype\t$amount\tna\tcomment
    """
    ts_str = timestr_est(event.timestamp)

    # Determine type string
    if event.event_type == EventType.SUBSCRIPTION:
        months = event.metadata.get("months", 1)
        type_str = "Sub" if months == 1 else f"Sub #{months}"
    elif event.event_type == EventType.SUBSCRIPTION_GIFT:
        type_str = "Sub"
    elif event.event_type == EventType.BITS:
        type_str = "Bits"
    elif event.event_type == EventType.TIP:
        is_test = event.metadata.get("is_test", False)
        type_str = "Tip_TEST" if is_test else "Tip"
    elif event.event_type == EventType.RAID:
        viewers = event.metadata.get("viewers", 0)
        type_str = f"Raid - {viewers}"
    elif event.event_type == EventType.RAFFLE:
        type_str = "Raffle"
    else:
        type_str = event.event_type.value

    gifter = event.gifter or ""
    supporter = event.user or "Unknown"
    amount = event.amount or 0.0
    comment = event.message or ""

    outstr = f"{ts_str}\t\t{gifter}\t{supporter}\t{type_str}\t${amount:0.2f}\tna\t{comment}"

    print(outstr, file=sys.stdout)
    sys.stdout.flush()

    print(outstr, file=sys.stderr)
    sys.stderr.flush()


def output_extra_event(event: Event) -> None:
    """
    Output extra event (replicates printextra).

    Format: "  message\n"
    """
    message = event.message or ""
    message = message.strip()

    print("  " + message + "\n", file=sys.stdout)
    sys.stdout.flush()

    print("  " + message + "\n", file=sys.stderr)
    sys.stderr.flush()


def output_state_event(event: Event) -> None:
    """
    Output stream state event (replicates out).

    Format: "timestamp message"
    """
    ts_str = timestr_est(event.timestamp)

    if event.event_type == EventType.STREAM_ONLINE:
        stream_type = event.metadata.get("type", "unknown")
        started_at = event.metadata.get("started_at", "unknown")
        msg = f"=== ONLINE (type={stream_type} @ {started_at} ==="
    elif event.event_type == EventType.STREAM_OFFLINE:
        msg = "=== OFFLINE ==="
    elif event.event_type == EventType.HYPE_TRAIN_BEGIN:
        msg = "=== HYPE TRAIN BEGIN ==="
    elif event.event_type == EventType.HYPE_TRAIN_END:
        level = event.metadata.get("level", 0)
        total = event.metadata.get("total", 0)
        msg = f"=== HYPE TRAIN END (level={level}, total={total}) ==="
    else:
        msg = f"=== {event.event_type.value.upper()} ==="

    print(ts_str, msg, file=sys.stdout)
    sys.stdout.flush()

    # Also log to stderr (replicates log() call in out())
    print(ts_str, msg, file=sys.stderr)
    sys.stderr.flush()
