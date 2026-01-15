"""
Event data structures for ongwatch.

This module defines the standardized event structure used to communicate
between backends and output handlers.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class EventType(Enum):
    """Enumeration of all event types in the ongwatch system"""

    # Support events (monetary)
    SUBSCRIPTION = "subscription"           # New sub or resub
    SUBSCRIPTION_GIFT = "sub_gift"          # Gifted sub
    BITS = "bits"                           # Twitch bits/cheers
    TIP = "tip"                             # StreamElements/StreamLabs donation
    RAID = "raid"                           # Incoming raid
    RAFFLE = "raffle"                       # Raffle winner

    # Chat events
    SONG_REQUEST = "song_request"           # !sr command

    # Stream state events
    STREAM_ONLINE = "stream_online"
    STREAM_OFFLINE = "stream_offline"
    HYPE_TRAIN_BEGIN = "hype_train_begin"
    HYPE_TRAIN_END = "hype_train_end"


@dataclass
class Event:
    """
    Standardized event structure for all ongwatch events.

    This structure provides a consistent interface for all output handlers
    while preserving all original data from different backends.
    """

    # Core fields - always present
    event_type: EventType
    timestamp: int                          # Unix timestamp
    backend: str                            # Source: "twitch", "streamelements", "streamlabs"

    # Common fields - present for most events (None if not applicable)
    user: Optional[str] = None              # Primary user (supporter, requester, raider)
    gifter: Optional[str] = None            # For gift subs
    amount: Optional[float] = None          # Monetary value in USD
    message: Optional[str] = None           # Comment, song request text, etc.

    # Event-specific fields
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional event-specific data

    # Original data preservation
    raw_data: Dict[str, Any] = field(default_factory=dict)  # Complete original event data

    def __post_init__(self) -> None:
        """Validate event structure after initialization"""
        if not isinstance(self.event_type, EventType):
            raise ValueError(f"event_type must be EventType enum, got {type(self.event_type)}")
        if not isinstance(self.backend, str) or not self.backend:
            raise ValueError("backend must be non-empty string")
        if not isinstance(self.timestamp, int) or self.timestamp <= 0:
            raise ValueError("timestamp must be positive integer")
