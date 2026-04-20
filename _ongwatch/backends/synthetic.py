"""Synthetic backend — emits one fixture event per event type for output testing.

Not in BACKEND_LIST; enable explicitly with --enable-backend synthetic.
"""
from __future__ import annotations

import argparse
import asyncio
import dataclasses
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from ..dispatcher import Dispatcher
from ..events import (CashSupportEvent, ChannelPointRedemptionEvent,
                      CharityDonationEvent, FollowEvent, GiftSubEvent,
                      GoalEvent, HypeTrainEvent, OngwatchEvent, PollEvent,
                      PredictionEvent, RaffleWinEvent, RaidEvent,
                      ShoutoutEvent, SongRequestEvent, StreamStateEvent,
                      SubscriptionEvent)

# Seconds to wait after start() is called before the first event is emitted.
# Gives outputs time to fully connect before the burst arrives.
_STARTUP_DELAY: float = 2.0

# Seconds between successive events.
_EVENT_INTERVAL: float = 0.5


# ---------------------------------------------------------------------------
# Fixture events — one (or a couple) of each type
# ---------------------------------------------------------------------------

def _fixtures() -> list[OngwatchEvent]:
    now = datetime.now(tz=timezone.utc)

    return [
        # --- Currently-emitted types (outputs return HANDLED for these) ---

        StreamStateEvent(
            timestamp=now, backend="synthetic", raw=None,
            state="online",
        ),
        CashSupportEvent(
            timestamp=now, backend="synthetic", raw=None,
            username="test_tipper", amount=10.00, kind="tip", comment="Great stream!",
        ),
        CashSupportEvent(
            timestamp=now, backend="synthetic", raw=None,
            username="test_cheerer", amount=1.00, kind="bits", comment=None,
        ),
        SubscriptionEvent(
            timestamp=now, backend="synthetic", raw=None,
            username="test_subscriber", tier=1, is_resub=False,
        ),
        SubscriptionEvent(
            timestamp=now, backend="synthetic", raw=None,
            username="test_resubber", tier=2, is_resub=True, months=6,
            message="6 months hype!",
        ),
        GiftSubEvent(
            timestamp=now, backend="synthetic", raw=None,
            gifter="test_gifter", recipients=["recipient_a", "recipient_b"],
            tier=1, count=2,
        ),
        GiftSubEvent(
            timestamp=now, backend="synthetic", raw=None,
            gifter=None, recipients=["anon_recipient"], tier=1, count=1,
        ),
        RaidEvent(
            timestamp=now, backend="synthetic", raw=None,
            from_channel="test_raider", viewer_count=42,
        ),
        HypeTrainEvent(
            timestamp=now, backend="synthetic", raw=None,
            kind="begin", level=1, total=500,
        ),
        HypeTrainEvent(
            timestamp=now, backend="synthetic", raw=None,
            kind="end", level=3, total=5000,
        ),
        SongRequestEvent(
            timestamp=now, backend="synthetic", raw=None,
            title="Test Song - Test Artist", requester="test_requester",
        ),
        RaffleWinEvent(
            timestamp=now, backend="synthetic", raw=None,
            winner="test_winner",
        ),
        StreamStateEvent(
            timestamp=now, backend="synthetic", raw=None,
            state="offline",
        ),

        # --- Defined/reserved types (outputs return REJECTED for these) ---

        FollowEvent(
            timestamp=now, backend="synthetic", raw=None,
            username="test_follower", followed_at=now,
        ),
        ChannelPointRedemptionEvent(
            timestamp=now, backend="synthetic", raw=None,
            username="test_redeemer", reward_title="Hydrate!", reward_cost=100,
            status="fulfilled",
        ),
        PollEvent(
            timestamp=now, backend="synthetic", raw=None,
            kind="end", title="Favourite colour?",
            choices=[{"title": "Red", "votes": 10}, {"title": "Blue", "votes": 7}],
            winning_choice="Red",
        ),
        PredictionEvent(
            timestamp=now, backend="synthetic", raw=None,
            kind="end", title="Will we beat the boss?",
            outcomes=[
                {"title": "Yes", "users": 30, "channel_points": 3000},
                {"title": "No",  "users": 12, "channel_points": 1200},
            ],
            winning_outcome="Yes",
        ),
        CharityDonationEvent(
            timestamp=now, backend="synthetic", raw=None,
            username="test_donor", amount=25.00, currency="USD",
            campaign_name="Test Charity Run",
        ),
        GoalEvent(
            timestamp=now, backend="synthetic", raw=None,
            kind="progress", goal_type="follower", current=750, target=1000,
        ),
        ShoutoutEvent(
            timestamp=now, backend="synthetic", raw=None,
            kind="received", channel="test_channel", viewer_count=200,
        ),
    ]


# ---------------------------------------------------------------------------
# Backend entry point
# ---------------------------------------------------------------------------

async def start(
    args: argparse.Namespace,
    creds: Dict[str, Any] | None,
    logger: logging.Logger,
    dispatcher: Dispatcher,
) -> None:
    fixtures = [dataclasses.replace(e, is_test=True) for e in _fixtures()]

    logger.info(
        f"Synthetic backend starting; will emit {len(fixtures)} events "
        f"in {_STARTUP_DELAY:.0f}s"
    )
    await asyncio.sleep(_STARTUP_DELAY)

    for event in fixtures:
        dispatcher.emit(event)
        logger.info(f"Emitted {type(event).__name__}")
        await asyncio.sleep(_EVENT_INTERVAL)

    logger.info("Synthetic backend done emitting; idling until shutdown")
    await asyncio.Event().wait()
