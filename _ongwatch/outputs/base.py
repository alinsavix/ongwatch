import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class OutputHandler(ABC):
    """Base class for all output handlers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.name = self.__class__.__name__

    @abstractmethod
    async def handle_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Process an event with the given type and data."""
        pass

    async def initialize(self) -> None:
        """Initialize the output handler. Override if needed."""
        pass

    async def shutdown(self) -> None:
        """Clean up resources. Override if needed."""
        pass




from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


# Base class for all Twitch events
@dataclass
class TwitchEvent:
    """Base class for all Twitch events."""
    event_id: str
    event_type: str
    event_timestamp: datetime
    version: str


# Common user information
@dataclass
class UserInfo:
    """Common user information across multiple events."""
    user_id: str
    user_login: str
    user_name: str


# Common broadcaster information
@dataclass
class BroadcasterInfo:
    """Common broadcaster information across multiple events."""
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str


# Common moderator information
@dataclass
class ModeratorInfo:
    """Common moderator information across multiple events."""
    moderator_user_id: str
    moderator_user_login: str
    moderator_user_name: str


# Common reward information
@dataclass
class RewardInfo:
    """Common channel point reward information."""
    id: str
    title: str
    cost: int
    prompt: str


# Subscription notification event
@dataclass
class ChannelSubscribeEvent(TwitchEvent):
    """Event for channel subscription notifications."""
    broadcaster_info: BroadcasterInfo
    user_info: UserInfo
    tier: str
    is_gift: bool


# Subscription gift event
@dataclass
class ChannelSubscriptionGiftEvent(TwitchEvent):
    """Event for channel subscription gift notifications."""
    broadcaster_info: BroadcasterInfo
    user_info: UserInfo
    total: int
    tier: str
    cumulative_total: Optional[int] = None
    is_anonymous: bool = False


# Subscription message event
@dataclass
class ChannelSubscriptionMessageEvent(TwitchEvent):
    """Event for resub messages."""
    broadcaster_info: BroadcasterInfo
    user_info: UserInfo
    tier: str
    message: str
    cumulative_months: int
    streak_months: Optional[int] = None
    duration_months: int = 1


# Cheer event
@dataclass
class ChannelCheerEvent(TwitchEvent):
    """Event for channel cheer/bits notifications."""
    broadcaster_info: BroadcasterInfo
    user_info: Optional[UserInfo]
    bits: int
    message: str
    is_anonymous: bool = False


# Raid event
@dataclass
class ChannelRaidEvent(TwitchEvent):
    """Event for channel raid notifications."""
    from_broadcaster_info: BroadcasterInfo
    to_broadcaster_info: BroadcasterInfo
    viewers: int


# Channel ban event
@dataclass
class ChannelBanEvent(TwitchEvent):
    """Event for channel ban notifications."""
    broadcaster_info: BroadcasterInfo
    user_info: UserInfo
    moderator_info: ModeratorInfo
    reason: str
    ends_at: Optional[datetime] = None
    is_permanent: bool = True


# Channel unban event
@dataclass
class ChannelUnbanEvent(TwitchEvent):
    """Event for channel unban notifications."""
    broadcaster_info: BroadcasterInfo
    user_info: UserInfo
    moderator_info: ModeratorInfo


# Moderator add event
@dataclass
class ChannelModeratorAddEvent(TwitchEvent):
    """Event for adding a moderator to a channel."""
    broadcaster_info: BroadcasterInfo
    user_info: UserInfo


# Moderator remove event
@dataclass
class ChannelModeratorRemoveEvent(TwitchEvent):
    """Event for removing a moderator from a channel."""
    broadcaster_info: BroadcasterInfo
    user_info: UserInfo


# Channel points custom reward add event
@dataclass
class ChannelPointsCustomRewardAddEvent(TwitchEvent):
    """Event for adding a custom channel points reward."""
    broadcaster_info: BroadcasterInfo
    reward: RewardInfo
    is_enabled: bool
    is_paused: bool
    is_in_stock: bool
    default_image: Dict[str, str]
    should_redemptions_skip_request_queue: bool
    max_per_stream: Optional[Dict[str, int]] = None
    max_per_user_per_stream: Optional[Dict[str, int]] = None
    global_cooldown: Optional[Dict[str, int]] = None
    background_color: Optional[str] = None
    image: Optional[Dict[str, str]] = None


# Channel points custom reward update event
@dataclass
class ChannelPointsCustomRewardUpdateEvent(TwitchEvent):
    """Event for updating a custom channel points reward."""
    broadcaster_info: BroadcasterInfo
    reward: RewardInfo
    is_enabled: bool
    is_paused: bool
    is_in_stock: bool
    default_image: Dict[str, str]
    should_redemptions_skip_request_queue: bool
    max_per_stream: Optional[Dict[str, int]] = None
    max_per_user_per_stream: Optional[Dict[str, int]] = None
    global_cooldown: Optional[Dict[str, int]] = None
    background_color: Optional[str] = None
    image: Optional[Dict[str, str]] = None


# Channel points custom reward remove event
@dataclass
class ChannelPointsCustomRewardRemoveEvent(TwitchEvent):
    """Event for removing a custom channel points reward."""
    broadcaster_info: BroadcasterInfo
    reward: RewardInfo
    is_enabled: bool
    is_paused: bool
    is_in_stock: bool
    default_image: Dict[str, str]
    should_redemptions_skip_request_queue: bool
    max_per_stream: Optional[Dict[str, int]] = None
    max_per_user_per_stream: Optional[Dict[str, int]] = None
    global_cooldown: Optional[Dict[str, int]] = None
    background_color: Optional[str] = None
    image: Optional[Dict[str, str]] = None


# Redemption status enum
class RedemptionStatus(str, Enum):
    UNFULFILLED = "unfulfilled"
    FULFILLED = "fulfilled"
    CANCELED = "canceled"


# Channel points custom reward redemption add event
@dataclass
class ChannelPointsCustomRewardRedemptionAddEvent(TwitchEvent):
    """Event for redeeming a custom channel points reward."""
    broadcaster_info: BroadcasterInfo
    user_info: UserInfo
    reward: RewardInfo
    redemption_id: str
    user_input: str
    status: RedemptionStatus
    redeemed_at: datetime


# Channel points custom reward redemption update event
@dataclass
class ChannelPointsCustomRewardRedemptionUpdateEvent(TwitchEvent):
    """Event for updating a custom channel points reward redemption."""
    broadcaster_info: BroadcasterInfo
    user_info: UserInfo
    reward: RewardInfo
    redemption_id: str
    user_input: str
    status: RedemptionStatus
    redeemed_at: datetime


# Poll status enum
class PollStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    ARCHIVED = "archived"


# Poll choice
@dataclass
class PollChoice:
    """A choice in a poll."""
    id: str
    title: str
    votes: int
    channel_points_votes: int
    bits_votes: int


# Channel poll begin event
@dataclass
class ChannelPollBeginEvent(TwitchEvent):
    """Event for starting a poll."""
    broadcaster_info: BroadcasterInfo
    poll_id: str
    title: str
    choices: List[PollChoice]
    bits_voting: Dict[str, Any]
    channel_points_voting: Dict[str, Any]
    started_at: datetime
    ends_at: datetime


# Channel poll progress event
@dataclass
class ChannelPollProgressEvent(TwitchEvent):
    """Event for poll progress updates."""
    broadcaster_info: BroadcasterInfo
    poll_id: str
    title: str
    choices: List[PollChoice]
    bits_voting: Dict[str, Any]
    channel_points_voting: Dict[str, Any]
    started_at: datetime
    ends_at: datetime


# Channel poll end event
@dataclass
class ChannelPollEndEvent(TwitchEvent):
    """Event for ending a poll."""
    broadcaster_info: BroadcasterInfo
    poll_id: str
    title: str
    choices: List[PollChoice]
    bits_voting: Dict[str, Any]
    channel_points_voting: Dict[str, Any]
    status: PollStatus
    started_at: datetime
    ended_at: datetime


# Prediction status enum
class PredictionStatus(str, Enum):
    ACTIVE = "active"
    LOCKED = "locked"
    RESOLVED = "resolved"
    CANCELED = "canceled"


# Prediction outcome
@dataclass
class PredictionOutcome:
    """An outcome in a prediction."""
    id: str
    title: str
    color: str
    users: int
    channel_points: int
    top_predictors: List[Dict[str, Any]]


# Channel prediction begin event
@dataclass
class ChannelPredictionBeginEvent(TwitchEvent):
    """Event for starting a prediction."""
    broadcaster_info: BroadcasterInfo
    prediction_id: str
    title: str
    outcomes: List[PredictionOutcome]
    started_at: datetime
    locks_at: datetime


# Channel prediction progress event
@dataclass
class ChannelPredictionProgressEvent(TwitchEvent):
    """Event for prediction progress updates."""
    broadcaster_info: BroadcasterInfo
    prediction_id: str
    title: str
    outcomes: List[PredictionOutcome]
    started_at: datetime
    locks_at: datetime


# Channel prediction lock event
@dataclass
class ChannelPredictionLockEvent(TwitchEvent):
    """Event for locking a prediction."""
    broadcaster_info: BroadcasterInfo
    prediction_id: str
    title: str
    outcomes: List[PredictionOutcome]
    status: PredictionStatus
    started_at: datetime
    locked_at: datetime


# Channel prediction end event
@dataclass
class ChannelPredictionEndEvent(TwitchEvent):
    """Event for ending a prediction."""
    broadcaster_info: BroadcasterInfo
    prediction_id: str
    title: str
    outcomes: List[PredictionOutcome]
    status: PredictionStatus
    started_at: datetime
    ended_at: datetime
    winning_outcome_id: Optional[str] = None


# Hype train contribution
@dataclass
class HypeTrainContribution:
    """A contribution to a hype train."""
    user_info: UserInfo
    type: str
    total: int


# Channel hype train begin event
@dataclass
class ChannelHypeTrainBeginEvent(TwitchEvent):
    """Event for starting a hype train."""
    broadcaster_info: BroadcasterInfo
    level: int
    total: int
    progress: int
    goal: int
    top_contributions: List[HypeTrainContribution]
    last_contribution: HypeTrainContribution
    started_at: datetime
    expires_at: datetime


# Channel hype train progress event
@dataclass
class ChannelHypeTrainProgressEvent(TwitchEvent):
    """Event for hype train progress updates."""
    broadcaster_info: BroadcasterInfo
    level: int
    total: int
    progress: int
    goal: int
    top_contributions: List[HypeTrainContribution]
    last_contribution: HypeTrainContribution
    started_at: datetime
    expires_at: datetime


# Channel hype train end event
@dataclass
class ChannelHypeTrainEndEvent(TwitchEvent):
    """Event for ending a hype train."""
    broadcaster_info: BroadcasterInfo
    level: int
    total: int
    top_contributions: List[HypeTrainContribution]
    started_at: datetime
    ended_at: datetime
    cooldown_ends_at: datetime


# Stream online event
@dataclass
class StreamOnlineEvent(TwitchEvent):
    """Event for stream going online."""
    broadcaster_info: BroadcasterInfo
    id: str
    type: str
    started_at: datetime


# Stream offline event
@dataclass
class StreamOfflineEvent(TwitchEvent):
    """Event for stream going offline."""
    broadcaster_info: BroadcasterInfo


# User update event
@dataclass
class UserUpdateEvent(TwitchEvent):
    """Event for user profile updates."""
    user_info: UserInfo
    email: Optional[str] = None
    description: Optional[str] = None


# MQTT Topic Names
class TwitchMQTTTopics:
    """MQTT topic names for Twitch events."""
    BASE_TOPIC = "twitch"

    # Channel events
    CHANNEL_SUBSCRIBE = f"{BASE_TOPIC}/channel/subscribe"
    CHANNEL_SUBSCRIPTION_GIFT = f"{BASE_TOPIC}/channel/subscription_gift"
    CHANNEL_SUBSCRIPTION_MESSAGE = f"{BASE_TOPIC}/channel/subscription_message"
    CHANNEL_CHEER = f"{BASE_TOPIC}/channel/cheer"
    CHANNEL_RAID = f"{BASE_TOPIC}/channel/raid"
    CHANNEL_BAN = f"{BASE_TOPIC}/channel/ban"
    CHANNEL_UNBAN = f"{BASE_TOPIC}/channel/unban"
    CHANNEL_MODERATOR_ADD = f"{BASE_TOPIC}/channel/moderator/add"
    CHANNEL_MODERATOR_REMOVE = f"{BASE_TOPIC}/channel/moderator/remove"

    # Channel points events
    CHANNEL_POINTS_REWARD_ADD = f"{BASE_TOPIC}/channel_points/reward/add"
    CHANNEL_POINTS_REWARD_UPDATE = f"{BASE_TOPIC}/channel_points/reward/update"
    CHANNEL_POINTS_REWARD_REMOVE = f"{BASE_TOPIC}/channel_points/reward/remove"
    CHANNEL_POINTS_REDEMPTION_ADD = f"{BASE_TOPIC}/channel_points/redemption/add"
    CHANNEL_POINTS_REDEMPTION_UPDATE = f"{BASE_TOPIC}/channel_points/redemption/update"

    # Poll events
    CHANNEL_POLL_BEGIN = f"{BASE_TOPIC}/channel/poll/begin"
    CHANNEL_POLL_PROGRESS = f"{BASE_TOPIC}/channel/poll/progress"
    CHANNEL_POLL_END = f"{BASE_TOPIC}/channel/poll/end"

    # Prediction events
    CHANNEL_PREDICTION_BEGIN = f"{BASE_TOPIC}/channel/prediction/begin"
    CHANNEL_PREDICTION_PROGRESS = f"{BASE_TOPIC}/channel/prediction/progress"
    CHANNEL_PREDICTION_LOCK = f"{BASE_TOPIC}/channel/prediction/lock"
    CHANNEL_PREDICTION_END = f"{BASE_TOPIC}/channel/prediction/end"

    # Hype train events
    CHANNEL_HYPE_TRAIN_BEGIN = f"{BASE_TOPIC}/channel/hype_train/begin"
    CHANNEL_HYPE_TRAIN_PROGRESS = f"{BASE_TOPIC}/channel/hype_train/progress"
    CHANNEL_HYPE_TRAIN_END = f"{BASE_TOPIC}/channel/hype_train/end"

    # Stream events
    STREAM_ONLINE = f"{BASE_TOPIC}/stream/online"
    STREAM_OFFLINE = f"{BASE_TOPIC}/stream/offline"

    # User events
    USER_UPDATE = f"{BASE_TOPIC}/user/update"

    @classmethod
    def get_topic_for_event(cls, event: TwitchEvent) -> str:
        """Get the appropriate MQTT topic for a given event."""
        event_class_name = event.__class__.__name__

        # Map event class names to topic attributes
        mapping = {
            "ChannelSubscribeEvent": cls.CHANNEL_SUBSCRIBE,
            "ChannelSubscriptionGiftEvent": cls.CHANNEL_SUBSCRIPTION_GIFT,
            "ChannelSubscriptionMessageEvent": cls.CHANNEL_SUBSCRIPTION_MESSAGE,
            "ChannelCheerEvent": cls.CHANNEL_CHEER,
            "ChannelRaidEvent": cls.CHANNEL_RAID,
            "ChannelBanEvent": cls.CHANNEL_BAN,
            "ChannelUnbanEvent": cls.CHANNEL_UNBAN,
            "ChannelModeratorAddEvent": cls.CHANNEL_MODERATOR_ADD,
            "ChannelModeratorRemoveEvent": cls.CHANNEL_MODERATOR_REMOVE,
            "ChannelPointsCustomRewardAddEvent": cls.CHANNEL_POINTS_REWARD_ADD,
            "ChannelPointsCustomRewardUpdateEvent": cls.CHANNEL_POINTS_REWARD_UPDATE,
            "ChannelPointsCustomRewardRemoveEvent": cls.CHANNEL_POINTS_REWARD_REMOVE,
            "ChannelPointsCustomRewardRedemptionAddEvent": cls.CHANNEL_POINTS_REDEMPTION_ADD,
            "ChannelPointsCustomRewardRedemptionUpdateEvent": cls.CHANNEL_POINTS_REDEMPTION_UPDATE,
            "ChannelPollBeginEvent": cls.CHANNEL_POLL_BEGIN,
            "ChannelPollProgressEvent": cls.CHANNEL_POLL_PROGRESS,
            "ChannelPollEndEvent": cls.CHANNEL_POLL_END,
            "ChannelPredictionBeginEvent": cls.CHANNEL_PREDICTION_BEGIN,
            "ChannelPredictionProgressEvent": cls.CHANNEL_PREDICTION_PROGRESS,
            "ChannelPredictionLockEvent": cls.CHANNEL_PREDICTION_LOCK,
            "ChannelPredictionEndEvent": cls.CHANNEL_PREDICTION_END,
            "ChannelHypeTrainBeginEvent": cls.CHANNEL_HYPE_TRAIN_BEGIN,
            "ChannelHypeTrainProgressEvent": cls.CHANNEL_HYPE_TRAIN_PROGRESS,
            "ChannelHypeTrainEndEvent": cls.CHANNEL_HYPE_TRAIN_END,
            "StreamOnlineEvent": cls.STREAM_ONLINE,
            "StreamOfflineEvent": cls.STREAM_OFFLINE,
            "UserUpdateEvent": cls.USER_UPDATE,
        }

        return mapping.get(event_class_name, f"{cls.BASE_TOPIC}/unknown")
