# EventSub message examples
See https://dev.twitch.tv/docs/eventsub/eventsub-reference/ for reference


## Stream comes online
```python
Event of type StreamOnlineEvent:
 twitchAPI.object.eventsub.StreamOnlineEvent(
    event = twitchAPI.object.eventsub.StreamOnlineData(
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            id = '41905330519', 
            started_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 3, 
                    microsecond = 0, 
                    minute = 46, 
                    month = 1, 
                    second = 23, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            type = 'live'
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 3, 
                    microsecond = 834808, 
                    minute = 26, 
                    month = 1, 
                    second = 38, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = 'de7b8293-bbe7-4d33-af8a-a8ee4220a5d8', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQgMoU-AkrRhCk2tgM09fcwBIGY2VsbC1h'
                }, 
            type = 'stream.online', 
            version = '1'
        )
)
```


## Chat message (just an emote)

```python
Event of type ChannelChatMessageEvent:
 twitchAPI.object.eventsub.ChannelChatMessageEvent(
    event = twitchAPI.object.eventsub.ChannelChatMessageData(
            badges = [
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '2024', 
                        info = '31', 
                        set_id = 'subscriber'
                    ), 
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '25000', 
                        info = '', 
                        set_id = 'bits'
                    )
                ], 
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            channel_points_custom_reward_id = None, 
            chatter_user_id = '548335835', 
            chatter_user_login = 'mrkenisi', 
            chatter_user_name = 'MrKenisi', 
            cheer = None, 
            color = '#E0467A', 
            message = twitchAPI.object.eventsub.ChatMessage(
                    fragments = [twitchAPI.object.eventsub.ChatMessageFragment(...)], 
                    text = 'ongHey'
                ), 
            message_id = '784f3f0e-f0c1-4d5b-ab0c-14ee8c08767d', 
            message_type = 'text', 
            reply = None
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 3, 
                    microsecond = 318788, 
                    minute = 26, 
                    month = 1, 
                    second = 24, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = 'afae4d97-e68a-4948-93d0-5a832e7897d7', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQgMoU-AkrRhCk2tgM09fcwBIGY2VsbC1h'
                }, 
            type = 'channel.chat.message', 
            version = '1'
        )
)
```


## chat msg with @tag and emote

```python
Event of type ChannelChatMessageEvent:
 twitchAPI.object.eventsub.ChannelChatMessageEvent(
    event = twitchAPI.object.eventsub.ChannelChatMessageData(
            badges = [
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '24', 
                        info = '33', 
                        set_id = 'subscriber'
                    ), 
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '1', 
                        info = '', 
                        set_id = 'clip-the-halls'
                    )
                ], 
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            channel_points_custom_reward_id = None, 
            chatter_user_id = '488837561', 
            chatter_user_login = 'sistergotgame222', 
            chatter_user_name = 'SisterGotGame222', 
            cheer = None, 
            color = '#F48DC0', 
            message = twitchAPI.object.eventsub.ChatMessage(
                    fragments = [
                            twitchAPI.object.eventsub.ChatMessageFragment(...), 
                            twitchAPI.object.eventsub.ChatMessageFragment(...), 
                            twitchAPI.object.eventsub.ChatMessageFragment(...), 
                            twitchAPI.object.eventsub.ChatMessageFragment(...)
                        ], 
                    text = 'hello @Jantha ongHug'
                ), 
            message_id = 'f1b84adb-35f6-49b0-9c78-7fcd16dbda8f', 
            message_type = 'text', 
            reply = None
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 3, 
                    microsecond = 318788, 
                    minute = 26, 
                    month = 1, 
                    second = 24, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = 'afae4d97-e68a-4948-93d0-5a832e7897d7', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQgMoU-AkrRhCk2tgM09fcwBIGY2VsbC1h'
                }, 
            type = 'channel.chat.message', 
            version = '1'
        )
)
```


## Cheer (with emote)

```python
Event of type ChannelChatMessageEvent:
 twitchAPI.object.eventsub.ChannelChatMessageEvent(
    event = twitchAPI.object.eventsub.ChannelChatMessageData(
            badges = [
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '1',
                        info = '',
                        set_id = 'moderator'
                    ),
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '3048',
                        info = '58',
                        set_id = 'subscriber'
                    ),
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '3',
                        info = '',
                        set_id = 'sub-gift-leader'
                    )
                ],
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            channel_points_custom_reward_id = None,
            chatter_user_id = '129765209',
            chatter_user_login = 'alinsa_vix',
            chatter_user_name = 'alinsa_vix',
            cheer = twitchAPI.object.eventsub.ChatMessageCheerMetadata(bits = 3),
            color = '#47D970',
            message = twitchAPI.object.eventsub.ChatMessage(
                    fragments = [
                            twitchAPI.object.eventsub.ChatMessageFragment(...),
                            twitchAPI.object.eventsub.ChatMessageFragment(...),
                            twitchAPI.object.eventsub.ChatMessageFragment(...),
                            twitchAPI.object.eventsub.ChatMessageFragment(...),
                            twitchAPI.object.eventsub.ChatMessageFragment(...),
                            twitchAPI.object.eventsub.ChatMessageFragment(...)
                        ],
                    text = 'Testing Cheer1  Testing Cheer2 ongHug'
                ),
            message_id = '7f28dde7-a846-43ca-bfed-1975f8992a52',
            message_type = 'text',
            reply = None
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 22,
                    microsecond = 811955,
                    minute = 42,
                    month = 1,
                    second = 0,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '986415af-db81-404d-b0a6-b3997c6ff621',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQq9npuZJpQSC2z7kzVRkmuhIGY2VsbC1h'
                },
            type = 'channel.chat.message',
            version = '1'
        )
)
```

```python
Event of type ChannelCheerEvent:
 twitchAPI.object.eventsub.ChannelCheerEvent(
    event = twitchAPI.object.eventsub.ChannelCheerData(
            bits = 3,
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            is_anonymous = False,
            message = 'Testing Cheer1  Testing Cheer2 ongHug',
            user_id = '129765209',
            user_login = 'alinsa_vix',
            user_name = 'alinsa_vix'
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 22,
                    microsecond = 377122,
                    minute = 42,
                    month = 1,
                    second = 2,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '9586da6d-099d-4ba0-b17a-40dfd44ed4e3',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQq9npuZJpQSC2z7kzVRkmuhIGY2VsbC1h'
                },
            type = 'channel.cheer',
            version = '1'
        )
)
```


## resub w/ chat notification

```python
Event of type ChannelSubscriptionMessageEvent:
 twitchAPI.object.eventsub.ChannelSubscriptionMessageEvent(
    event = twitchAPI.object.eventsub.ChannelSubscriptionMessageData(
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            cumulative_months = 54, 
            duration_months = 10, 
            message = twitchAPI.object.eventsub.SubscriptionMessage(
                emotes = None,     text = 'Is that your new home?'), 
            tier = '1000', 
            user_id = '65500430', 
            user_login = 'radiocom1g', 
            user_name = 'Radiocom1G'
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 3, 
                    microsecond = 310825, 
                    minute = 26, 
                    month = 1, 
                    second = 34, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = '4459b3c6-e326-4335-9161-4bcf6f7cddf0', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQgMoU-AkrRhCk2tgM09fcwBIGY2VsbC1h'
                }, 
            type = 'channel.subscription.message', 
            version = '1'
        )
)
```

```python
Event of type ChannelChatNotificationEvent:
 twitchAPI.object.eventsub.ChannelChatNotificationEvent(
    event = twitchAPI.object.eventsub.ChannelChatNotificationData(
            announcement = None, 
            badges = [
                    twitchAPI.object.eventsub.Badge(
                        id = '48', 
                        info = '54', 
                        set_id = 'subscriber'
                    ), 
                    twitchAPI.object.eventsub.Badge(
                        id = '1', 
                        info = '', 
                        set_id = 'premium'
                    )
                ], 
            bits_badge_tier = None, 
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            charity_donation = None, 
            chatter_is_anonymous = False, 
            chatter_user_id = '65500430', 
            chatter_user_login = 'radiocom1g', 
            chatter_user_name = 'Radiocom1G', 
            color = '#1E90FF', 
            community_sub_gift = None, 
            gift_paid_upgrade = None, 
            message = twitchAPI.object.eventsub.Message(
                    fragments = [twitchAPI.object.eventsub.MessageFragment(...)], 
                    text = 'Is that your new home?'
                ), 
            message_id = '77186201-f5c4-424f-98a8-7e0904834947', 
            notice_type = 'resub', 
            pay_it_forward = None, 
            prime_paid_upgrade = None, 
            raid = None, 
            resub = twitchAPI.object.eventsub.ResubNoticeMetadata(
                    cumulative_months = 54, 
                    duration_months = 10, 
                    gifter_is_anonymous = None, 
                    gifter_user_id = None, 
                    gifter_user_login = None, 
                    gifter_user_name = None, 
                    is_gift = False, 
                    is_prime = False, 
                    streak_months = None, 
                    sub_tier = '1000'
                ), 
            sub = None, 
            sub_gift = None, 
            system_message = 'Radiocom1G subscribed at ...ubscribed for 54 months!', 
            unraid = None
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 3, 
                    microsecond = 98444, 
                    minute = 26, 
                    month = 1, 
                    second = 25, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = '793138ea-6e00-4b4d-87f5-fbb165459111', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQgMoU-AkrRhCk2tgM09fcwBIGY2VsbC1h'
                }, 
            type = 'channel.chat.notification', 
            version = '1'
        )
)
```


## Stream Offline

```python
Event of type StreamOfflineEvent:
 twitchAPI.object.eventsub.StreamOfflineEvent(
    event = twitchAPI.object.eventsub.StreamOfflineData(
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng'
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 3, 
                    microsecond = 449336, 
                    minute = 26, 
                    month = 1, 
                    second = 38, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = '1384b65c-d8f7-4d8b-8758-c2dfdef2d8e5', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQgMoU-AkrRhCk2tgM09fcwBIGY2VsbC1h'
                }, 
            type = 'stream.offline', 
            version = '1'
        )
)
```


## Stream Online (again)

```python
Event of type StreamOnlineEvent:
 twitchAPI.object.eventsub.StreamOnlineEvent(
    event = twitchAPI.object.eventsub.StreamOnlineData(
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            id = '41905468503', 
            started_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 3, 
                    microsecond = 0, 
                    minute = 56, 
                    month = 1, 
                    second = 39, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            type = 'live'
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 3, 
                    microsecond = 834808, 
                    minute = 26, 
                    month = 1, 
                    second = 38, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = 'de7b8293-bbe7-4d33-af8a-a8ee4220a5d8', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQgMoU-AkrRhCk2tgM09fcwBIGY2VsbC1h'
                }, 
            type = 'stream.online', 
            version = '1'
        )
)
```


## Stream info update

```python
Event of type ChannelUpdateEvent:
 twitchAPI.object.eventsub.ChannelUpdateEvent(
    event = twitchAPI.object.eventsub.ChannelUpdateData(
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            category_id = '26936',
            category_name = 'Music',
            content_classification_labels = [],
            language = 'en',
            title = '[Rerun] Hanging out and c...st (Jon is on vacation!)'
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 22,
                    microsecond = 899336,
                    minute = 46,
                    month = 1,
                    second = 19,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '8e7b68e9-f0d3-4a09-b667-b43ae45b591e',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQf28JfByRR3yog592vGMhABIGY2VsbC1h'
                },
            type = 'channel.update',
            version = '2'
        )
)
```


## Ad Break

```python
Event of type ChannelAdBreakBeginEvent:
 twitchAPI.object.eventsub.ChannelAdBreakBeginEvent(
    event = twitchAPI.object.eventsub.ChannelAdBreakBeginData(
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            duration_seconds = 180, 
            is_automatic = True, 
            requester_user_id = '156801396', 
            requester_user_login = 'jonathanong', 
            requester_user_name = 'JonathanOng', 
            started_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 381578, 
                    minute = 6, 
                    month = 1, 
                    second = 47, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                )
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 3, 
                    microsecond = 259232, 
                    minute = 26, 
                    month = 1, 
                    second = 22, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = 'ee89f7ae-3ee8-44ba-a6d0-343314fba25b', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQgMoU-AkrRhCk2tgM09fcwBIGY2VsbC1h'
                }, 
            type = 'channel.ad_break.begin', 
            version = '1'
        )
)
```


## Resub

```python
Event of type ChannelSubscriptionMessageEvent:
 twitchAPI.object.eventsub.ChannelSubscriptionMessageEvent(
    event = twitchAPI.object.eventsub.ChannelSubscriptionMessageData(
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            cumulative_months = 11, 
            duration_months = 6, 
            message = twitchAPI.object.eventsub.SubscriptionMessage(
                emotes = None,     text = 'peepoHi'), 
            tier = '1000', 
            user_id = '128168490', 
            user_login = 'madmill', 
            user_name = 'madmill'
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 104368, 
                    minute = 23, 
                    month = 1, 
                    second = 33, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = '455a63ef-72b7-48dd-972b-a8772ad9cbad', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ95fz49LLT5qCvNPvKQa5lhIGY2VsbC1h'
                }, 
            type = 'channel.subscription.message', 
            version = '1'
        )
)
```

```python
Event of type ChannelChatNotificationEvent:
 twitchAPI.object.eventsub.ChannelChatNotificationEvent(
    event = twitchAPI.object.eventsub.ChannelChatNotificationData(
            announcement = None, 
            badges = [
                    twitchAPI.object.eventsub.Badge(
                        id = '6', 
                        info = '11', 
                        set_id = 'subscriber'
                    ), 
                    twitchAPI.object.eventsub.Badge(
                        id = '1', 
                        info = '', 
                        set_id = 'bits'
                    )
                ], 
            bits_badge_tier = None, 
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            charity_donation = None, 
            chatter_is_anonymous = False, 
            chatter_user_id = '128168490', 
            chatter_user_login = 'madmill', 
            chatter_user_name = 'madmill', 
            color = '#DAA520', 
            community_sub_gift = None, 
            gift_paid_upgrade = None, 
            message = twitchAPI.object.eventsub.Message(
                    fragments = [twitchAPI.object.eventsub.MessageFragment(...)], 
                    text = 'peepoHi'
                ), 
            message_id = '492189f8-7e5c-43ce-a9df-73fd733e069f', 
            notice_type = 'resub', 
            pay_it_forward = None, 
            prime_paid_upgrade = None, 
            raid = None, 
            resub = twitchAPI.object.eventsub.ResubNoticeMetadata(
                    cumulative_months = 11, 
                    duration_months = 6, 
                    gifter_is_anonymous = None, 
                    gifter_user_id = None, 
                    gifter_user_login = None, 
                    gifter_user_name = None, 
                    is_gift = False, 
                    is_prime = False, 
                    streak_months = 11, 
                    sub_tier = '1000'
                ), 
            sub = None, 
            sub_gift = None, 
            system_message = 'madmill subscribed at Tie...ly on a 11 month streak!', 
            unraid = None
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 716133, 
                    minute = 23, 
                    month = 1, 
                    second = 20, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = 'a453caf8-41b9-4618-a37c-c24cca1a8c12', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ95fz49LLT5qCvNPvKQa5lhIGY2VsbC1h'
                }, 
            type = 'channel.chat.notification', 
            version = '1'
        )
)
```


## Single gift sub (I think)

```python
Event of type ChannelSubscribeEvent:
 twitchAPI.object.eventsub.ChannelSubscribeEvent(
    event = twitchAPI.object.eventsub.ChannelSubscribeData(
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            is_gift = True, 
            tier = '3000', 
            user_id = '116695665', 
            user_login = 'goombanna', 
            user_name = 'Goombanna'
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 75699, 
                    minute = 23, 
                    month = 1, 
                    second = 32, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = '6247911e-3f01-492c-90fe-f25cd0666ed6', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ95fz49LLT5qCvNPvKQa5lhIGY2VsbC1h'
                }, 
            type = 'channel.subscribe', 
            version = '1'
        )
)
```

```python
Event of type ChannelSubscriptionGiftEvent:
 twitchAPI.object.eventsub.ChannelSubscriptionGiftEvent(
    event = twitchAPI.object.eventsub.ChannelSubscriptionGiftData(
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            cumulative_total = 7, 
            is_anonymous = False, 
            tier = '3000', 
            total = 1, 
            user_id = '70681848', 
            user_login = 'wrongtown', 
            user_name = 'Wrongtown'
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 812150, 
                    minute = 23, 
                    month = 1, 
                    second = 32, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = '3e7c4d7c-9f1d-43be-9e06-972b1461b227', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ95fz49LLT5qCvNPvKQa5lhIGY2VsbC1h'
                }, 
            type = 'channel.subscription.gift', 
            version = '1'
        )
)
```

```python
Event of type ChannelChatNotificationEvent:
 twitchAPI.object.eventsub.ChannelChatNotificationEvent(
    event = twitchAPI.object.eventsub.ChannelChatNotificationData(
            announcement = None, 
            badges = [
                    twitchAPI.object.eventsub.Badge(
                        id = '3003', 
                        info = '4', 
                        set_id = 'subscriber'
                    ), 
                    twitchAPI.object.eventsub.Badge(
                        id = '5', 
                        info = '', 
                        set_id = 'sub-gifter'
                    )
                ], 
            bits_badge_tier = None, 
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            charity_donation = None, 
            chatter_is_anonymous = False, 
            chatter_user_id = '70681848', 
            chatter_user_login = 'wrongtown', 
            chatter_user_name = 'Wrongtown', 
            color = '#1E90FF', 
            community_sub_gift = None, 
            gift_paid_upgrade = None, 
            message = twitchAPI.object.eventsub.Message(fragments = [], text = ''), 
            message_id = '04cb8a71-c6ba-4c18-ad7f-d2fe18136b0e', 
            notice_type = 'sub_gift', 
            pay_it_forward = None, 
            prime_paid_upgrade = None, 
            raid = None, 
            resub = None, 
            sub = None, 
            sub_gift = twitchAPI.object.eventsub.SubGiftNoticeMetadata(
                    community_gift_id = None, 
                    cumulative_total = 7, 
                    duration_months = 1, 
                    recipient_user_id = '116695665', 
                    recipient_user_login = 'goombanna', 
                    recipient_user_name = 'Goombanna', 
                    sub_tier = '3000'
                ), 
            system_message = 'Wrongtown gifted a Tier 3...ift Subs in the channel!', 
            unraid = None
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 716133, 
                    minute = 23, 
                    month = 1, 
                    second = 20, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = 'a453caf8-41b9-4618-a37c-c24cca1a8c12', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ95fz49LLT5qCvNPvKQa5lhIGY2VsbC1h'
                }, 
            type = 'channel.chat.notification', 
            version = '1'
        )
)
```


## Incoming raid

```python
Event of type ChannelRaidEvent:
 twitchAPI.object.eventsub.ChannelRaidEvent(
    event = twitchAPI.object.eventsub.ChannelRaidData(
            from_broadcaster_user_id = '116695665', 
            from_broadcaster_user_login = 'goombanna', 
            from_broadcaster_user_name = 'Goombanna', 
            to_broadcaster_user_id = '156801396', 
            to_broadcaster_user_login = 'jonathanong', 
            to_broadcaster_user_name = 'JonathanOng', 
            viewers = 38
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {
                    'from_broadcaster_user_id': '', 
                    'to_broadcaster_user_id': '156801396'
                }, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 8538, 
                    minute = 23, 
                    month = 1, 
                    second = 29, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = '00fea56e-be19-4c1d-981e-58ceab645a35', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ95fz49LLT5qCvNPvKQa5lhIGY2VsbC1h'
                }, 
            type = 'channel.raid', 
            version = '1'
        )
)
```

```python
Event of type ChannelChatNotificationEvent:
 twitchAPI.object.eventsub.ChannelChatNotificationEvent(
    event = twitchAPI.object.eventsub.ChannelChatNotificationData(
            announcement = None, 
            badges = [
                    twitchAPI.object.eventsub.Badge(
                        id = '3000', 
                        info = '2', 
                        set_id = 'subscriber'
                    ), 
                    twitchAPI.object.eventsub.Badge(
                        id = '1', 
                        info = '', 
                        set_id = 'premium'
                    )
                ], 
            bits_badge_tier = None, 
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            charity_donation = None, 
            chatter_is_anonymous = False, 
            chatter_user_id = '116695665', 
            chatter_user_login = 'goombanna', 
            chatter_user_name = 'Goombanna', 
            color = '#CE00FF', 
            community_sub_gift = None, 
            gift_paid_upgrade = None, 
            message = twitchAPI.object.eventsub.Message(fragments = [], text = ''), 
            message_id = 'dca5f1de-3409-40d1-bd14-fc5d271a5d1e', 
            notice_type = 'raid', 
            pay_it_forward = None, 
            prime_paid_upgrade = None, 
            raid = twitchAPI.object.eventsub.RaidNoticeMetadata(
                    profile_image_url = 'https://static-cdn.jtvnw....rofile_image-300x300.png', 
                    user_id = '116695665', 
                    user_login = 'goombanna', 
                    user_name = 'Goombanna', 
                    viewer_count = 38
                ), 
            resub = None, 
            sub = None, 
            sub_gift = None, 
            system_message = '38 raiders from Goombanna have joined!', 
            unraid = None
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 716133, 
                    minute = 23, 
                    month = 1, 
                    second = 20, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = 'a453caf8-41b9-4618-a37c-c24cca1a8c12', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ95fz49LLT5qCvNPvKQa5lhIGY2VsbC1h'
                }, 
            type = 'channel.chat.notification', 
            version = '1'
        )
)
```


## Basic resub (I think)

```python
Event of type ChannelSubscriptionMessageEvent:
 twitchAPI.object.eventsub.ChannelSubscriptionMessageEvent(
    event = twitchAPI.object.eventsub.ChannelSubscriptionMessageData(
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            cumulative_months = 4, 
            duration_months = 3, 
            message = twitchAPI.object.eventsub.SubscriptionMessage(
                    emotes = None, 
                    text = "Hope you're having a great stream mate!"
                ), 
            tier = '3000', 
            user_id = '70681848', 
            user_login = 'wrongtown', 
            user_name = 'Wrongtown'
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 104368, 
                    minute = 23, 
                    month = 1, 
                    second = 33, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = '455a63ef-72b7-48dd-972b-a8772ad9cbad', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ95fz49LLT5qCvNPvKQa5lhIGY2VsbC1h'
                }, 
            type = 'channel.subscription.message', 
            version = '1'
        )
)
```

```python
Event of type ChannelChatNotificationEvent:
 twitchAPI.object.eventsub.ChannelChatNotificationEvent(
    event = twitchAPI.object.eventsub.ChannelChatNotificationData(
            announcement = None, 
            badges = [
                    twitchAPI.object.eventsub.Badge(
                        id = '3003', 
                        info = '4', 
                        set_id = 'subscriber'
                    ), 
                    twitchAPI.object.eventsub.Badge(
                        id = '5', 
                        info = '', 
                        set_id = 'sub-gifter'
                    )
                ], 
            bits_badge_tier = None, 
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            charity_donation = None, 
            chatter_is_anonymous = False, 
            chatter_user_id = '70681848', 
            chatter_user_login = 'wrongtown', 
            chatter_user_name = 'Wrongtown', 
            color = '#1E90FF', 
            community_sub_gift = None, 
            gift_paid_upgrade = None, 
            message = twitchAPI.object.eventsub.Message(
                    fragments = [twitchAPI.object.eventsub.MessageFragment(...)], 
                    text = "Hope you're having a great stream mate!"
                ), 
            message_id = 'b3bf5119-4abb-45af-a4dc-e7cb97275983', 
            notice_type = 'resub', 
            pay_it_forward = None, 
            prime_paid_upgrade = None, 
            raid = None, 
            resub = twitchAPI.object.eventsub.ResubNoticeMetadata(
                    cumulative_months = 4, 
                    duration_months = 3, 
                    gifter_is_anonymous = None, 
                    gifter_user_id = None, 
                    gifter_user_login = None, 
                    gifter_user_name = None, 
                    is_gift = False, 
                    is_prime = False, 
                    streak_months = 4, 
                    sub_tier = '3000'
                ), 
            sub = None, 
            sub_gift = None, 
            system_message = 'Wrongtown subscribed at T...tly on a 4 month streak!', 
            unraid = None
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 716133, 
                    minute = 23, 
                    month = 1, 
                    second = 20, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = 'a453caf8-41b9-4618-a37c-c24cca1a8c12', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ95fz49LLT5qCvNPvKQa5lhIGY2VsbC1h'
                }, 
            type = 'channel.chat.notification', 
            version = '1'
        )
)
```


## Followed

```python
Event of type ChannelFollowEvent:
 twitchAPI.object.eventsub.ChannelFollowEvent(
    event = twitchAPI.object.eventsub.ChannelFollowData(
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            followed_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 7, 
                    microsecond = 98885, 
                    minute = 56, 
                    month = 1, 
                    second = 41, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            user_id = '713205238', 
            user_login = 'gingerbeardnz', 
            user_name = 'GingerbeardNZ'
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {
                    'broadcaster_user_id': '156801396', 
                    'moderator_user_id': '156801396'
                }, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 848969, 
                    minute = 23, 
                    month = 1, 
                    second = 21, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = 'daaba828-59f9-4ff1-b73d-385dad0a0e4b', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ95fz49LLT5qCvNPvKQa5lhIGY2VsbC1h'
                }, 
            type = 'channel.follow', 
            version = '2'
        )
)
```


## Message effect - Power up

```python
Event of type ChannelChatMessageEvent:
 twitchAPI.object.eventsub.ChannelChatMessageEvent(
    event = twitchAPI.object.eventsub.ChannelChatMessageData(
            badges = [
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '1',
                        info = '',
                        set_id = 'moderator'
                    ),
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '3048',
                        info = '58',
                        set_id = 'subscriber'
                    ),
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '3',
                        info = '',
                        set_id = 'sub-gift-leader'
                    )
                ],
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            channel_points_custom_reward_id = None,
            chatter_user_id = '129765209',
            chatter_user_login = 'alinsa_vix',
            chatter_user_name = 'alinsa_vix',
            cheer = None,
            color = '#47D970',
            message = twitchAPI.object.eventsub.ChatMessage(
                    fragments = [twitchAPI.object.eventsub.ChatMessageFragment(...)],
                    text = 'Just one week until Jon returns to making music!'
                ),
            message_id = '46d614d5-3bc8-4c4b-8dcf-f9781cce1786',
            message_type = 'power_ups_message_effect',
            reply = None
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 23,
                    microsecond = 778495,
                    minute = 8,
                    month = 1,
                    second = 10,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '7a491e00-c610-4b5d-92fe-b8373ecaefa1',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQN1cxIgTrS-SiCRGINxJVihIGY2VsbC1h'
                },
            type = 'channel.chat.message',
            version = '1'
        )
)
```

```python
Event of type ChannelPointsAutomaticRewardRedemptionAddEvent:
 twitchAPI.object.eventsub.ChannelPointsAutomaticRewardRedemptionAddEvent(
    event = twitchAPI.object.eventsub.ChannelPointsAutomaticRewardRedemptionAddData(
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            id = 'cd3829f8-5d2b-4d9f-9ba8-085b060a8ca4',
            message = twitchAPI.object.eventsub.RewardMessage(
                    emotes = None,
                    text = 'Just one week until Jon returns to making music!'
                ),
            redeemed_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 23,
                    microsecond = 798954,
                    minute = 9,
                    month = 1,
                    second = 38,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            reward = twitchAPI.object.eventsub.AutomaticReward(
                    cost = 0,
                    type = 'message_effect',
                    unlocked_emote = None
                ),
            user_id = '129765209',
            user_input = 'Just one week until Jon returns to making music!',
            user_login = 'alinsa_vix',
            user_name = 'alinsa_vix'
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 23,
                    microsecond = 743044,
                    minute = 8,
                    month = 1,
                    second = 13,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '5d2f1eed-ea35-42e3-baea-887ecad336af',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQN1cxIgTrS-SiCRGINxJVihIGY2VsbC1h'
                },
            type = 'channel.channel_points_au...ic_reward_redemption.add',
            version = '1'
        )
)
```


## Gigantify emote

```python
Event of type ChannelChatMessageEvent:
 twitchAPI.object.eventsub.ChannelChatMessageEvent(
    event = twitchAPI.object.eventsub.ChannelChatMessageData(
            badges = [
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '1',
                        info = '',
                        set_id = 'moderator'
                    ),
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '3048',
                        info = '58',
                        set_id = 'subscriber'
                    ),
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '3',
                        info = '',
                        set_id = 'sub-gift-leader'
                    )
                ],
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            channel_points_custom_reward_id = None,
            chatter_user_id = '129765209',
            chatter_user_login = 'alinsa_vix',
            chatter_user_name = 'alinsa_vix',
            cheer = None,
            color = '#47D970',
            message = twitchAPI.object.eventsub.ChatMessage(
                    fragments = [twitchAPI.object.eventsub.ChatMessageFragment(...)],
                    text = 'ongHug'
                ),
            message_id = '8fe92a78-5276-4677-a830-24c33837481e',
            message_type = 'power_ups_gigantified_emote',
            reply = None
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 23,
                    microsecond = 161884,
                    minute = 10,
                    month = 1,
                    second = 32,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '06e8671f-1f37-420c-9b47-e4bf100cd2ed',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQ3ZkR38znQ3aD4OyxtLMyWRIGY2VsbC1h'
                },
            type = 'channel.chat.message',
            version = '1'
        )
)
```

```python
Event of type ChannelPointsAutomaticRewardRedemptionAddEvent:
 twitchAPI.object.eventsub.ChannelPointsAutomaticRewardRedemptionAddEvent(
    event = twitchAPI.object.eventsub.ChannelPointsAutomaticRewardRedemptionAddData(
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            id = '6609cca5-9d19-4dc2-a2df-2320469df785',
            message = twitchAPI.object.eventsub.RewardMessage(
                    emotes = [twitchAPI.object.eventsub.Emote(...)],
                    text = 'ongHug'
                ),
            redeemed_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 23,
                    microsecond = 890676,
                    minute = 11,
                    month = 1,
                    second = 25,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            reward = twitchAPI.object.eventsub.AutomaticReward(
                    cost = 0,
                    type = 'gigantify_an_emote',
                    unlocked_emote = None
                ),
            user_id = '129765209',
            user_input = None,
            user_login = 'alinsa_vix',
            user_name = 'alinsa_vix'
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 23,
                    microsecond = 656983,
                    minute = 10,
                    month = 1,
                    second = 35,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '4da27502-f676-4a18-96fc-4ea6e3947545',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQ3ZkR38znQ3aD4OyxtLMyWRIGY2VsbC1h'
                },
            type = 'channel.channel_points_au...ic_reward_redemption.add',
            version = '1'
        )
)
```


## Modify and use emote

```python
Event of type ChannelPointsAutomaticRewardRedemptionAddEvent:
 twitchAPI.object.eventsub.ChannelPointsAutomaticRewardRedemptionAddEvent(
    event = twitchAPI.object.eventsub.ChannelPointsAutomaticRewardRedemptionAddData(
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            id = '8553436d-fed7-4f9a-a3f5-d5a99312dc2a',
            message = twitchAPI.object.eventsub.RewardMessage(
                emotes = None,     text = ''),
            redeemed_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 23,
                    microsecond = 86077,
                    minute = 14,
                    month = 1,
                    second = 41,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            reward = twitchAPI.object.eventsub.AutomaticReward(
                    cost = 960,
                    type = 'chosen_modified_sub_emote_unlock',
                    unlocked_emote = None
                ),
            user_id = '129765209',
            user_input = None,
            user_login = 'alinsa_vix',
            user_name = 'alinsa_vix'
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 23,
                    microsecond = 740442,
                    minute = 12,
                    month = 1,
                    second = 28,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '4a7177e0-fe7f-4ca7-bbb2-d58a8ae897a7',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQglH84UB3SkqgkyuFBD681RIGY2VsbC1h'
                },
            type = 'channel.channel_points_au...ic_reward_redemption.add',
            version = '1'
        )
)
```

```python
Event of type ChannelChatMessageEvent:
 twitchAPI.object.eventsub.ChannelChatMessageEvent(
    event = twitchAPI.object.eventsub.ChannelChatMessageData(
            badges = [
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '1',
                        info = '',
                        set_id = 'moderator'
                    ),
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '3048',
                        info = '58',
                        set_id = 'subscriber'
                    ),
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '3',
                        info = '',
                        set_id = 'sub-gift-leader'
                    )
                ],
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            channel_points_custom_reward_id = None,
            chatter_user_id = '129765209',
            chatter_user_login = 'alinsa_vix',
            chatter_user_name = 'alinsa_vix',
            cheer = None,
            color = '#47D970',
            message = twitchAPI.object.eventsub.ChatMessage(
                    fragments = [twitchAPI.object.eventsub.ChatMessageFragment(...)],
                    text = 'ongHug_TK'
                ),
            message_id = '113635dc-c453-4e1d-a01f-b088354c338e',
            message_type = 'text',
            reply = None
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 23,
                    microsecond = 244123,
                    minute = 12,
                    month = 1,
                    second = 25,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = 'd3a5f861-56f1-410d-9654-c74e4d330180',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQglH84UB3SkqgkyuFBD681RIGY2VsbC1h'
                },
            type = 'channel.chat.message',
            version = '1'
        )
)
```


## 5000 channel point redeem

```python
Event of type ChannelPointsCustomRewardRedemptionAddEvent:
 twitchAPI.object.eventsub.ChannelPointsCustomRewardRedemptionAddEvent(
    event = twitchAPI.object.eventsub.ChannelPointsCustomRewardRedemptionData(
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            id = 'ee076d26-764c-44e7-b724-88e0b516f866',
            redeemed_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 23,
                    microsecond = 424946,
                    minute = 15,
                    month = 1,
                    second = 54,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            reward = twitchAPI.object.eventsub.Reward(
                    cost = 5000,
                    id = '7c992c5f-6c54-4d54-a9cf-ea4a7efb547c',
                    prompt = 'this shows you upcoming special events',
                    title = 'special'
                ),
            status = 'unfulfilled',
            user_id = '129765209',
            user_input = '',
            user_login = 'alinsa_vix',
            user_name = 'alinsa_vix'
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'reward_id': ''},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 23,
                    microsecond = 762747,
                    minute = 12,
                    month = 1,
                    second = 29,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '5742bfa0-c38d-4fb5-827e-8fdd6d65f958',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQglH84UB3SkqgkyuFBD681RIGY2VsbC1h'
                },
            type = 'channel.channel_points_cu...om_reward_redemption.add',
            version = '1'
        )
)
```


## Chat message highlight (channel points)

```python
Event of type ChannelChatMessageEvent:
 twitchAPI.object.eventsub.ChannelChatMessageEvent(
    event = twitchAPI.object.eventsub.ChannelChatMessageData(
            badges = [
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '1',
                        info = '',
                        set_id = 'moderator'
                    ),
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '3048',
                        info = '58',
                        set_id = 'subscriber'
                    ),
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '3',
                        info = '',
                        set_id = 'sub-gift-leader'
                    )
                ],
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            channel_points_custom_reward_id = None,
            chatter_user_id = '129765209',
            chatter_user_login = 'alinsa_vix',
            chatter_user_name = 'alinsa_vix',
            cheer = None,
            color = '#47D970',
            message = twitchAPI.object.eventsub.ChatMessage(
                    fragments = [twitchAPI.object.eventsub.ChatMessageFragment(...)],
                    text = 'Wheeee, testing.'
                ),
            message_id = '82b48d02-7c25-4813-b7ea-06d92bd923c3',
            message_type = 'channel_points_highlighted',
            reply = None
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 23,
                    microsecond = 244123,
                    minute = 12,
                    month = 1,
                    second = 25,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = 'd3a5f861-56f1-410d-9654-c74e4d330180',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQglH84UB3SkqgkyuFBD681RIGY2VsbC1h'
                },
            type = 'channel.chat.message',
            version = '1'
        )
)
```

```python
Event of type ChannelPointsAutomaticRewardRedemptionAddEvent:
 twitchAPI.object.eventsub.ChannelPointsAutomaticRewardRedemptionAddEvent(
    event = twitchAPI.object.eventsub.ChannelPointsAutomaticRewardRedemptionAddData(
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            id = '42d8d3e7-5164-40e5-b4e7-9d59fde4d2c8',
            message = twitchAPI.object.eventsub.RewardMessage(
                emotes = None,     text = 'Wheeee, testing.'),
            redeemed_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 23,
                    microsecond = 778299,
                    minute = 17,
                    month = 1,
                    second = 10,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            reward = twitchAPI.object.eventsub.AutomaticReward(
                    cost = 1600,
                    type = 'send_highlighted_message',
                    unlocked_emote = None
                ),
            user_id = '129765209',
            user_input = 'Wheeee, testing.',
            user_login = 'alinsa_vix',
            user_name = 'alinsa_vix'
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 23,
                    microsecond = 740442,
                    minute = 12,
                    month = 1,
                    second = 28,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '4a7177e0-fe7f-4ca7-bbb2-d58a8ae897a7',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQglH84UB3SkqgkyuFBD681RIGY2VsbC1h'
                },
            type = 'channel.channel_points_au...ic_reward_redemption.add',
            version = '1'
        )
)
```


## gigantify emote with text

```python
Event of type ChannelChatMessageEvent:
 twitchAPI.object.eventsub.ChannelChatMessageEvent(
    event = twitchAPI.object.eventsub.ChannelChatMessageData(
            badges = [
                    twitchAPI.object.eventsub.ChatMessageBadge(
                        id = '3024', 
                        info = '32', 
                        set_id = 'subscriber'
                    )
                ], 
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            channel_points_custom_reward_id = None, 
            chatter_user_id = '66818147', 
            chatter_user_login = 'coreytownz', 
            chatter_user_name = 'COREYTOWNZ', 
            cheer = None, 
            color = '#DC143C', 
            message = twitchAPI.object.eventsub.ChatMessage(
                    fragments = [
                            twitchAPI.object.eventsub.ChatMessageFragment(...), 
                            twitchAPI.object.eventsub.ChatMessageFragment(...)
                        ], 
                    text = 'omg he said my name then the thing barbSuffer'
                ), 
            message_id = '4e86db69-27ce-4bc3-8eb0-6c05b0ee9440', 
            message_type = 'power_ups_gigantified_emote', 
            reply = None
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 942330, 
                    minute = 23, 
                    month = 1, 
                    second = 19, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = '7cd0d0a5-3245-4247-9e79-f3d4b7e0f664', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ95fz49LLT5qCvNPvKQa5lhIGY2VsbC1h'
                }, 
            type = 'channel.chat.message', 
            version = '1'
        )
)
```

```python
Event of type ChannelPointsAutomaticRewardRedemptionAddEvent:
 twitchAPI.object.eventsub.ChannelPointsAutomaticRewardRedemptionAddEvent(
    event = twitchAPI.object.eventsub.ChannelPointsAutomaticRewardRedemptionAddData(
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            id = '9cf3bf8a-6eb7-4b91-8cfd-e19d66886b97', 
            message = twitchAPI.object.eventsub.RewardMessage(
                    emotes = [twitchAPI.object.eventsub.Emote(...)], 
                    text = 'omg he said my name then the thing barbSuffer'
                ), 
            redeemed_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 8, 
                    microsecond = 489753, 
                    minute = 44, 
                    month = 1, 
                    second = 20, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            reward = twitchAPI.object.eventsub.AutomaticReward(
                    cost = 0, 
                    type = 'gigantify_an_emote', 
                    unlocked_emote = None
                ), 
            user_id = '66818147', 
            user_input = 'omg he said my name then the thing', 
            user_login = 'coreytownz', 
            user_name = 'COREYTOWNZ'
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 605871, 
                    minute = 23, 
                    month = 1, 
                    second = 23, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = 'b4389edd-9bb0-4288-b4fe-5971cc41e227', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ95fz49LLT5qCvNPvKQa5lhIGY2VsbC1h'
                }, 
            type = 'channel.channel_points_au...ic_reward_redemption.add', 
            version = '1'
        )
)
```


## Raid out + Offline

```python
Event of type ChannelRaidEvent:
 twitchAPI.object.eventsub.ChannelRaidEvent(
    event = twitchAPI.object.eventsub.ChannelRaidData(
            from_broadcaster_user_id = '156801396', 
            from_broadcaster_user_login = 'jonathanong', 
            from_broadcaster_user_name = 'JonathanOng', 
            to_broadcaster_user_id = '806872144', 
            to_broadcaster_user_login = 'coreyclowns', 
            to_broadcaster_user_name = 'COREYCLOWNS', 
            viewers = 141
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {
                    'from_broadcaster_user_id': '156801396', 
                    'to_broadcaster_user_id': ''
                }, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 371106, 
                    minute = 23, 
                    month = 1, 
                    second = 29, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = '18cd7ad3-6365-448d-b0b8-56578767d01e', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ95fz49LLT5qCvNPvKQa5lhIGY2VsbC1h'
                }, 
            type = 'channel.raid', 
            version = '1'
        )
)
```

```python
Event of type StreamOfflineEvent:
 twitchAPI.object.eventsub.StreamOfflineEvent(
    event = twitchAPI.object.eventsub.StreamOfflineData(
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng'
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 629925, 
                    minute = 23, 
                    month = 1, 
                    second = 37, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = 'daeb293b-5148-4bd8-8847-1c4a76e60b91', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ95fz49LLT5qCvNPvKQa5lhIGY2VsbC1h'
                }, 
            type = 'stream.offline', 
            version = '1'
        )
)
```


## Single direct sub


```python
Event of type ChannelSubscribeEvent:
 twitchAPI.object.eventsub.ChannelSubscribeEvent(
    event = twitchAPI.object.eventsub.ChannelSubscribeData(
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            is_gift = False, 
            tier = '1000', 
            user_id = '65394146', 
            user_login = 'echodrone_', 
            user_name = 'echodrone_'
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 75699, 
                    minute = 23, 
                    month = 1, 
                    second = 32, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = '6247911e-3f01-492c-90fe-f25cd0666ed6', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ95fz49LLT5qCvNPvKQa5lhIGY2VsbC1h'
                }, 
            type = 'channel.subscribe', 
            version = '1'
        )
)
```

```python
Event of type ChannelSubscriptionMessageEvent:
 twitchAPI.object.eventsub.ChannelSubscriptionMessageEvent(
    event = twitchAPI.object.eventsub.ChannelSubscriptionMessageData(
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            cumulative_months = 20, 
            duration_months = 1, 
            message = twitchAPI.object.eventsub.SubscriptionMessage(
                    emotes = None, 
                    text = 'Hope I did this right. Dy...a thing without glkasses'
                ), 
            tier = '1000', 
            user_id = '65394146', 
            user_login = 'echodrone_', 
            user_name = 'echodrone_'
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 104368, 
                    minute = 23, 
                    month = 1, 
                    second = 33, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = '455a63ef-72b7-48dd-972b-a8772ad9cbad', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ95fz49LLT5qCvNPvKQa5lhIGY2VsbC1h'
                }, 
            type = 'channel.subscription.message', 
            version = '1'
        )
)
```

```python
Event of type ChannelChatNotificationEvent:
 twitchAPI.object.eventsub.ChannelChatNotificationEvent(
    event = twitchAPI.object.eventsub.ChannelChatNotificationData(
            announcement = None, 
            badges = [
                    twitchAPI.object.eventsub.Badge(
                        id = '12', 
                        info = '20', 
                        set_id = 'subscriber'
                    ), 
                    twitchAPI.object.eventsub.Badge(
                        id = '1', 
                        info = '', 
                        set_id = 'glhf-pledge'
                    )
                ], 
            bits_badge_tier = None, 
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            charity_donation = None, 
            chatter_is_anonymous = False, 
            chatter_user_id = '65394146', 
            chatter_user_login = 'echodrone_', 
            chatter_user_name = 'echodrone_', 
            color = '#E3A4DF', 
            community_sub_gift = None, 
            gift_paid_upgrade = None, 
            message = twitchAPI.object.eventsub.Message(
                    fragments = [twitchAPI.object.eventsub.MessageFragment(...)], 
                    text = 'Hope I did this right. Dy...a thing without glkasses'
                ), 
            message_id = '3d2753b7-cc3f-488d-b014-be2b847a287e', 
            notice_type = 'resub', 
            pay_it_forward = None, 
            prime_paid_upgrade = None, 
            raid = None, 
            resub = twitchAPI.object.eventsub.ResubNoticeMetadata(
                    cumulative_months = 20, 
                    duration_months = 1, 
                    gifter_is_anonymous = None, 
                    gifter_user_id = None, 
                    gifter_user_login = None, 
                    gifter_user_name = None, 
                    is_gift = False, 
                    is_prime = False, 
                    streak_months = None, 
                    sub_tier = '1000'
                ), 
            sub = None, 
            sub_gift = None, 
            system_message = 'echodrone_ subscribed at ...ubscribed for 20 months!', 
            unraid = None
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 4, 
                    microsecond = 716133, 
                    minute = 23, 
                    month = 1, 
                    second = 20, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = 'a453caf8-41b9-4618-a37c-c24cca1a8c12', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ95fz49LLT5qCvNPvKQa5lhIGY2VsbC1h'
                }, 
            type = 'channel.chat.notification', 
            version = '1'
        )
)
```


## Subscription ended

```python
Event of type ChannelSubscriptionEndEvent:
 twitchAPI.object.eventsub.ChannelSubscriptionEndEvent(
    event = twitchAPI.object.eventsub.ChannelSubscribeData(
            broadcaster_user_id = '156801396', 
            broadcaster_user_login = 'jonathanong', 
            broadcaster_user_name = 'JonathanOng', 
            is_gift = False, 
            tier = '1000', 
            user_id = '112501443', 
            user_login = 'dockellen', 
            user_name = 'DocKellen'
        ), 
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'}, 
            cost = 0, 
            created_at = datetime(
                    day = 9, 
                    fold = 0, 
                    hour = 11, 
                    microsecond = 77714, 
                    minute = 50, 
                    month = 1, 
                    second = 2, 
                    tzinfo = dateutil.tz.tz.tzutc(), 
                    year = 2025
                ), 
            id = 'db7b812e-a3b4-492d-beb8-ad4f86005cba', 
            status = 'enabled', 
            transport = {
                    'method': 'websocket', 
                    'session_id': 'AgoQ5KfytbATT3aMbHCEr7UjWBIGY2VsbC1h'
                }, 
            type = 'channel.subscription.end', 
            version = '1'
        )
)
```


## 3 month gift sub

```python
Event of type ChannelSubscribeEvent:
 twitchAPI.object.eventsub.ChannelSubscribeEvent(
    event = twitchAPI.object.eventsub.ChannelSubscribeData(
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            is_gift = True,
            tier = '1000',
            user_id = '196034182',
            user_login = 'sukisox',
            user_name = 'SukiSox'
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 22,
                    microsecond = 799457,
                    minute = 15,
                    month = 1,
                    second = 15,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '766065df-fb72-41ed-ba5f-805c8836490e',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQNiKBYZbgRy-Tim5hh6QGlxIGY2VsbC1h'
                },
            type = 'channel.subscribe',
            version = '1'
        )
)
```

```python
Event of type ChannelSubscriptionGiftEvent:
 twitchAPI.object.eventsub.ChannelSubscriptionGiftEvent(
    event = twitchAPI.object.eventsub.ChannelSubscriptionGiftData(
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            cumulative_total = 233,
            is_anonymous = False,
            tier = '1000',
            total = 1,
            user_id = '129765209',
            user_login = 'alinsa_vix',
            user_name = 'alinsa_vix'
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 22,
                    microsecond = 523307,
                    minute = 15,
                    month = 1,
                    second = 16,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = 'bc96b76d-7bde-4e38-9ef0-937373979867',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQNiKBYZbgRy-Tim5hh6QGlxIGY2VsbC1h'
                },
            type = 'channel.subscription.gift',
            version = '1'
        )
)
```

```python
Event of type ChannelChatNotificationEvent:
 twitchAPI.object.eventsub.ChannelChatNotificationEvent(
    event = twitchAPI.object.eventsub.ChannelChatNotificationData(
            announcement = None,
            badges = [
                    twitchAPI.object.eventsub.Badge(
                        id = '1',
                        info = '',
                        set_id = 'moderator'
                    ),
                    twitchAPI.object.eventsub.Badge(
                        id = '3048',
                        info = '58',
                        set_id = 'subscriber'
                    )
                ],
            bits_badge_tier = None,
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            charity_donation = None,
            chatter_is_anonymous = False,
            chatter_user_id = '129765209',
            chatter_user_login = 'alinsa_vix',
            chatter_user_name = 'alinsa_vix',
            color = '#47D970',
            community_sub_gift = None,
            gift_paid_upgrade = None,
            message = twitchAPI.object.eventsub.Message(fragments = [], text = ''),
            message_id = '0f93b076-362c-44f8-af2c-4e0c330d336a',
            notice_type = 'sub_gift',
            pay_it_forward = None,
            prime_paid_upgrade = None,
            raid = None,
            resub = None,
            sub = None,
            sub_gift = twitchAPI.object.eventsub.SubGiftNoticeMetadata(
                    community_gift_id = None,
                    cumulative_total = 233,
                    duration_months = 3,
                    recipient_user_id = '196034182',
                    recipient_user_login = 'sukisox',
                    recipient_user_name = 'SukiSox',
                    sub_tier = '1000'
                ),
            system_message = 'alinsa_vix gifted 3 month...3 months in the channel!',
            unraid = None
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 22,
                    microsecond = 719652,
                    minute = 15,
                    month = 1,
                    second = 6,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '64fa32a6-6ce9-491b-9de1-015bcea9fed6',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQNiKBYZbgRy-Tim5hh6QGlxIGY2VsbC1h'
                },
            type = 'channel.chat.notification',
            version = '1'
        )
)
```


## 3 random gift subs

```python
Event of type ChannelSubscriptionGiftEvent:
 twitchAPI.object.eventsub.ChannelSubscriptionGiftEvent(
    event = twitchAPI.object.eventsub.ChannelSubscriptionGiftData(
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            cumulative_total = 236,
            is_anonymous = False,
            tier = '1000',
            total = 3,
            user_id = '129765209',
            user_login = 'alinsa_vix',
            user_name = 'alinsa_vix'
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 22,
                    microsecond = 249474,
                    minute = 37,
                    month = 1,
                    second = 6,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '1276a08d-b556-463d-8323-765ba39b932f',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQCDtrbrOnQ1epail91UOY9xIGY2VsbC1h'
                },
            type = 'channel.subscription.gift',
            version = '1'
        )
)
```

```python
Event of type ChannelChatNotificationEvent:
 twitchAPI.object.eventsub.ChannelChatNotificationEvent(
    event = twitchAPI.object.eventsub.ChannelChatNotificationData(
            announcement = None,
            badges = [
                    twitchAPI.object.eventsub.Badge(
                        id = '1',
                        info = '',
                        set_id = 'moderator'
                    ),
                    twitchAPI.object.eventsub.Badge(
                        id = '3048',
                        info = '58',
                        set_id = 'subscriber'
                    )
                ],
            bits_badge_tier = None,
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            charity_donation = None,
            chatter_is_anonymous = False,
            chatter_user_id = '129765209',
            chatter_user_login = 'alinsa_vix',
            chatter_user_name = 'alinsa_vix',
            color = '#47D970',
            community_sub_gift = twitchAPI.object.eventsub.CommunitySubGiftNoticeMetadata(
                    cumulative_total = 236,
                    id = '5635721670473954276',
                    sub_tier = '1000',
                    total = 3
                ),
            gift_paid_upgrade = None,
            message = twitchAPI.object.eventsub.Message(fragments = [], text = ''),
            message_id = '27c8afe2-5e3b-4669-9c44-ff051a6b0c89',
            notice_type = 'community_sub_gift',
            pay_it_forward = None,
            prime_paid_upgrade = None,
            raid = None,
            resub = None,
            sub = None,
            sub_gift = None,
            system_message = 'alinsa_vix is gifting 3 T...l of 236 in the channel!',
            unraid = None
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 22,
                    microsecond = 487455,
                    minute = 36,
                    month = 1,
                    second = 57,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '1b4f7a9f-ea62-40ae-8211-00bcb9adc9cb',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQCDtrbrOnQ1epail91UOY9xIGY2VsbC1h'
                },
            type = 'channel.chat.notification',
            version = '1'
        )
)
```

```python
Event of type ChannelSubscribeEvent:
 twitchAPI.object.eventsub.ChannelSubscribeEvent(
    event = twitchAPI.object.eventsub.ChannelSubscribeData(
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            is_gift = True,
            tier = '1000',
            user_id = '793205179',
            user_login = 'grimrosegamer',
            user_name = 'grimrosegamer'
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 22,
                    microsecond = 570812,
                    minute = 37,
                    month = 1,
                    second = 5,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '35e2288b-56fb-4848-82bc-b59c694f3412',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQCDtrbrOnQ1epail91UOY9xIGY2VsbC1h'
                },
            type = 'channel.subscribe',
            version = '1'
        )
)
```

```python
Event of type ChannelSubscribeEvent:
 twitchAPI.object.eventsub.ChannelSubscribeEvent(
    event = twitchAPI.object.eventsub.ChannelSubscribeData(
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            is_gift = True,
            tier = '1000',
            user_id = '175855855',
            user_login = 'tickticktonton',
            user_name = 'tickticktonton'
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 22,
                    microsecond = 570812,
                    minute = 37,
                    month = 1,
                    second = 5,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '35e2288b-56fb-4848-82bc-b59c694f3412',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQCDtrbrOnQ1epail91UOY9xIGY2VsbC1h'
                },
            type = 'channel.subscribe',
            version = '1'
        )
)
```

```python
Event of type ChannelSubscribeEvent:
 twitchAPI.object.eventsub.ChannelSubscribeEvent(
    event = twitchAPI.object.eventsub.ChannelSubscribeData(
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            is_gift = True,
            tier = '1000',
            user_id = '409758029',
            user_login = 'itssxnpai',
            user_name = 'ItsSxnpai'
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 22,
                    microsecond = 570812,
                    minute = 37,
                    month = 1,
                    second = 5,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '35e2288b-56fb-4848-82bc-b59c694f3412',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQCDtrbrOnQ1epail91UOY9xIGY2VsbC1h'
                },
            type = 'channel.subscribe',
            version = '1'
        )
)
```

```python
Event of type ChannelChatNotificationEvent:
 twitchAPI.object.eventsub.ChannelChatNotificationEvent(
    event = twitchAPI.object.eventsub.ChannelChatNotificationData(
            announcement = None,
            badges = [
                    twitchAPI.object.eventsub.Badge(
                        id = '1',
                        info = '',
                        set_id = 'moderator'
                    ),
                    twitchAPI.object.eventsub.Badge(
                        id = '3048',
                        info = '58',
                        set_id = 'subscriber'
                    ),
                    twitchAPI.object.eventsub.Badge(
                        id = '3',
                        info = '',
                        set_id = 'sub-gift-leader'
                    )
                ],
            bits_badge_tier = None,
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            charity_donation = None,
            chatter_is_anonymous = False,
            chatter_user_id = '129765209',
            chatter_user_login = 'alinsa_vix',
            chatter_user_name = 'alinsa_vix',
            color = '#47D970',
            community_sub_gift = None,
            gift_paid_upgrade = None,
            message = twitchAPI.object.eventsub.Message(fragments = [], text = ''),
            message_id = '1b51657d-96c3-4023-b8c6-ee774495310a',
            notice_type = 'sub_gift',
            pay_it_forward = None,
            prime_paid_upgrade = None,
            raid = None,
            resub = None,
            sub = None,
            sub_gift = twitchAPI.object.eventsub.SubGiftNoticeMetadata(
                    community_gift_id = '5635721670473954276',
                    cumulative_total = 0,
                    duration_months = 1,
                    recipient_user_id = '793205179',
                    recipient_user_login = 'grimrosegamer',
                    recipient_user_name = 'grimrosegamer',
                    sub_tier = '1000'
                ),
            system_message = 'alinsa_vix gifted a Tier 1 sub to grimrosegamer!',
            unraid = None
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 22,
                    microsecond = 487455,
                    minute = 36,
                    month = 1,
                    second = 57,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '1b4f7a9f-ea62-40ae-8211-00bcb9adc9cb',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQCDtrbrOnQ1epail91UOY9xIGY2VsbC1h'
                },
            type = 'channel.chat.notification',
            version = '1'
        )
)
```

```python
Event of type ChannelChatNotificationEvent:
 twitchAPI.object.eventsub.ChannelChatNotificationEvent(
    event = twitchAPI.object.eventsub.ChannelChatNotificationData(
            announcement = None,
            badges = [
                    twitchAPI.object.eventsub.Badge(
                        id = '1',
                        info = '',
                        set_id = 'moderator'
                    ),
                    twitchAPI.object.eventsub.Badge(
                        id = '3048',
                        info = '58',
                        set_id = 'subscriber'
                    ),
                    twitchAPI.object.eventsub.Badge(
                        id = '3',
                        info = '',
                        set_id = 'sub-gift-leader'
                    )
                ],
            bits_badge_tier = None,
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            charity_donation = None,
            chatter_is_anonymous = False,
            chatter_user_id = '129765209',
            chatter_user_login = 'alinsa_vix',
            chatter_user_name = 'alinsa_vix',
            color = '#47D970',
            community_sub_gift = None,
            gift_paid_upgrade = None,
            message = twitchAPI.object.eventsub.Message(fragments = [], text = ''),
            message_id = '02eef388-734e-4745-9e96-119f621c66b3',
            notice_type = 'sub_gift',
            pay_it_forward = None,
            prime_paid_upgrade = None,
            raid = None,
            resub = None,
            sub = None,
            sub_gift = twitchAPI.object.eventsub.SubGiftNoticeMetadata(
                    community_gift_id = '5635721670473954276',
                    cumulative_total = 0,
                    duration_months = 1,
                    recipient_user_id = '409758029',
                    recipient_user_login = 'itssxnpai',
                    recipient_user_name = 'ItsSxnpai',
                    sub_tier = '1000'
                ),
            system_message = 'alinsa_vix gifted a Tier 1 sub to ItsSxnpai!',
            unraid = None
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 22,
                    microsecond = 487455,
                    minute = 36,
                    month = 1,
                    second = 57,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '1b4f7a9f-ea62-40ae-8211-00bcb9adc9cb',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQCDtrbrOnQ1epail91UOY9xIGY2VsbC1h'
                },
            type = 'channel.chat.notification',
            version = '1'
        )
)
```

```python
Event of type ChannelChatNotificationEvent:
 twitchAPI.object.eventsub.ChannelChatNotificationEvent(
    event = twitchAPI.object.eventsub.ChannelChatNotificationData(
            announcement = None,
            badges = [
                    twitchAPI.object.eventsub.Badge(
                        id = '1',
                        info = '',
                        set_id = 'moderator'
                    ),
                    twitchAPI.object.eventsub.Badge(
                        id = '3048',
                        info = '58',
                        set_id = 'subscriber'
                    ),
                    twitchAPI.object.eventsub.Badge(
                        id = '3',
                        info = '',
                        set_id = 'sub-gift-leader'
                    )
                ],
            bits_badge_tier = None,
            broadcaster_user_id = '156801396',
            broadcaster_user_login = 'jonathanong',
            broadcaster_user_name = 'JonathanOng',
            charity_donation = None,
            chatter_is_anonymous = False,
            chatter_user_id = '129765209',
            chatter_user_login = 'alinsa_vix',
            chatter_user_name = 'alinsa_vix',
            color = '#47D970',
            community_sub_gift = None,
            gift_paid_upgrade = None,
            message = twitchAPI.object.eventsub.Message(fragments = [], text = ''),
            message_id = '5edd4cca-a39e-41be-b4fb-daae6f70a961',
            notice_type = 'sub_gift',
            pay_it_forward = None,
            prime_paid_upgrade = None,
            raid = None,
            resub = None,
            sub = None,
            sub_gift = twitchAPI.object.eventsub.SubGiftNoticeMetadata(
                    community_gift_id = '5635721670473954276',
                    cumulative_total = 0,
                    duration_months = 1,
                    recipient_user_id = '175855855',
                    recipient_user_login = 'tickticktonton',
                    recipient_user_name = 'tickticktonton',
                    sub_tier = '1000'
                ),
            system_message = 'alinsa_vix gifted a Tier 1 sub to tickticktonton!',
            unraid = None
        ),
    subscription = twitchAPI.object.eventsub.Subscription(
            condition = {'broadcaster_user_id': '156801396', 'user_id': '156801396'},
            cost = 0,
            created_at = datetime(
                    day = 9,
                    fold = 0,
                    hour = 22,
                    microsecond = 487455,
                    minute = 36,
                    month = 1,
                    second = 57,
                    tzinfo = dateutil.tz.tz.tzutc(),
                    year = 2025
                ),
            id = '1b4f7a9f-ea62-40ae-8211-00bcb9adc9cb',
            status = 'enabled',
            transport = {
                    'method': 'websocket',
                    'session_id': 'AgoQCDtrbrOnQ1epail91UOY9xIGY2VsbC1h'
                },
            type = 'channel.chat.notification',
            version = '1'
        )
)
```
