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

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the output handler. Override if needed."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Clean up resources. Override if needed."""
        pass


# FIXME: Should be in something MQTT-specific
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
    # def get_topic_for_event(cls, event: TwitchEvent) -> str:
    def get_topic_for_event(cls, event_type: str) -> str:
        """Get the appropriate MQTT topic for a given event."""
        event_class_name = event_type.__class__.__name__

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

        return f"{cls.BASE_TOPIC}/unknown"
        # return mapping.get(event_class_name, f"{cls.BASE_TOPIC}/unknown")
