from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(kw_only=True)
class OngwatchEvent:
    timestamp: datetime
    backend: str        # "twitch", "streamelements", "streamlabs"
    raw: Any            # original backend payload
    is_test: bool = False


# ---------------------------------------------------------------------------
# Currently emitted
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class CashSupportEvent(OngwatchEvent):
    username: str
    amount: float
    kind: str              # "bits" / "tip" / "donation"
    comment: str | None = None


@dataclass(kw_only=True)
class SubscriptionEvent(OngwatchEvent):
    username: str
    tier: int              # 1 / 2 / 3
    is_resub: bool
    months: int | None = None
    message: str | None = None


@dataclass(kw_only=True)
class GiftSubEvent(OngwatchEvent):
    recipients: list[str]
    tier: int
    count: int
    gifter: str | None = None   # None = anonymous


@dataclass(kw_only=True)
class RaidEvent(OngwatchEvent):
    from_channel: str
    viewer_count: int


@dataclass(kw_only=True)
class StreamStateEvent(OngwatchEvent):
    state: str             # "online" / "offline"


@dataclass(kw_only=True)
class HypeTrainEvent(OngwatchEvent):
    kind: str              # "begin" / "end"
    level: int
    total: int


@dataclass(kw_only=True)
class SongRequestEvent(OngwatchEvent):
    title: str
    requester: str | None = None


@dataclass(kw_only=True)
class RaffleWinEvent(OngwatchEvent):
    winner: str


# ---------------------------------------------------------------------------
# Defined/reserved — backends not yet subscribed to these EventSub events
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class FollowEvent(OngwatchEvent):
    username: str
    followed_at: datetime


@dataclass(kw_only=True)
class ChannelPointRedemptionEvent(OngwatchEvent):
    username: str
    reward_title: str
    reward_cost: int
    status: str
    user_input: str | None = None


@dataclass(kw_only=True)
class PollEvent(OngwatchEvent):
    kind: str              # "begin" / "progress" / "end"
    title: str
    choices: list[dict[str, Any]]
    winning_choice: str | None = None


@dataclass(kw_only=True)
class PredictionEvent(OngwatchEvent):
    kind: str              # "begin" / "progress" / "locked" / "end"
    title: str
    outcomes: list[dict[str, Any]]
    winning_outcome: str | None = None


@dataclass(kw_only=True)
class CharityDonationEvent(OngwatchEvent):
    username: str
    amount: float
    currency: str
    campaign_name: str


@dataclass(kw_only=True)
class GoalEvent(OngwatchEvent):
    kind: str              # "begin" / "progress" / "end"
    goal_type: str
    current: int
    target: int


@dataclass(kw_only=True)
class ShoutoutEvent(OngwatchEvent):
    kind: str              # "sent" / "received"
    channel: str
    viewer_count: int | None = None
