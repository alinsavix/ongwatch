# MQTT Topic Hierarchy

## Structure

```
{channel}/stream/status
{channel}/stream/viewers
{channel}/stream/mode

{channel}/songqueue/head
{channel}/songqueue/current
{channel}/songqueue/request

{channel}/support/direct   (e.g. cash, tips)
{channel}/support/sub
{channel}/support/giftsub

{channel}/raid/incoming
{channel}/raid/outgoing
{channel}/hypetrain/status

{channel}/raffle/win
{channel}/raffle/queue

{channel}/{subsystem}/*

{channel}/heartbeat
```

`{channel}` is the streamer's channel name (e.g. `jonathanong`).

One subsystem we know we'll use is the ojbpm tempo sync:

```
{channel}/ojbpm/current_bpm
{channel}/ojbpm/looper_slot
{channel}/ojbpm/loop_length_bars
{channel}/ojbpm/loop_length_secs
{channel}/ojbpm/playback_start_time
{channel}/ojbpm/playback_state
```

## Retained messages and QoS

| Topic | Retained | QoS | Notes |
|---|---|---|---|
| `{channel}/stream/status` | ✓ | 1 | Current stream state |
| `{channel}/stream/viewers` | ✓ | 1 | Current viewer count |
| `{channel}/stream/mode` | ✓ | 1 | e.g. learning / looping / concert grand |
| `{channel}/songqueue/head` | ✓ | 1 | Currently playing song |
| `{channel}/songqueue/current` | ✓ | 1 | The full queue in order, current song first |
| `{channel}/songqueue/request` | ✗ | 1 | A discrete event for a user submitting a request |
| `{channel}/support/direct | ✗ | 1 | Direct support (payments, cheers) |
| `{channel}/support/sub | ✗ | 1 | Direct subscriptions |
| `{channel}/support/giftsub | ✗ | 1 | Gift subs/gift sub bombs |
| `{channel}/raid/incoming | ✗ | 1 | Incoming raid event |
| `{channel}/raid/outgoing | ✗ | 1 | Outgoing raid event |
| `{channel}/hypetrain/status` | ✓ | 1 | Current hype train status (active/inactive/progress) |
| `{channel}/raffle/win` | ✗ | 1 | New raffle winner |
| `{channel}/raffle/queue` | ✓ | 1 | Current raffle queue, oldest raffle first |
| `{channel}/{ojbpm}/*` | ✓ | 1 | Current tempo tracking info (handled externally) |
| `{channel}/{backend}/*` | ? | 1 | Various other published info by other tasks |
| `{channel}/{backend}/heartbeat` | ✗ | 0 | Watchdog for various external processes, not sure how best to handle this |
| `{channel}/heartbeat` | ✗ | 0 | Watchdog tick; loss is acceptable |

Most topics are retained so a subscriber that connects mid-stream immediately
receives the current condition without replaying event history.

## Useful wildcard subscriptions

| Pattern | Matches |
|---|---|
| `{channel}/#` | Everything |
| `{channel}/support/#` | All incoming money |
| `{channel}/raid/#` | Incoming and outgoing raids |
| `{channel}/stream/#` | All stream state |
| `{channel}/ojbpm/#` | All looper and tempo matching state |

## Payload envelope

Every message published by ongwatch uses this JSON envelope:

```json
{
  "v": 1,
  "timestamp": "2026-04-18T20:00:00Z",
  "backend": "twitch",
  "event_type": "cash_support",
  "data": { },
  "raw": { }
}
```

| Field | Description |
|---|---|
| `v` | Payload schema version. Additive changes (new fields) do not increment this. Breaking changes (removed/renamed fields, restructured `data`) increment to `2`. |
| `timestamp` | ISO 8601 UTC timestamp of the event. |
| `backend` | Source backend: `twitch`, `streamelements`, or `streamlabs`. |
| `event_type` | Matches the final path segment of the topic (e.g. `cash_support`, `subscription`). |
| `data` | Normalized, backend-agnostic event fields. |
| `raw` | Raw payload received from the backend, as-is. May be `null` if the backend provided nothing serializable. |

## Presence / Last Will and Testament

On connect, ongwatch:
1. Registers a LWT: topic `{channel}/presence`, payload `"offline"`, retain=true, QoS=1.
2. Immediately publishes `"online"` to `{channel}/presence`, retain=true, QoS=1.

On clean shutdown, publishes `"offline"` before closing the connection. On
crash or lost connection, the broker fires the LWT automatically.

## `data` fields by event type

### `cash_support`
```json
{ "username": "...", "amount": 5.00, "kind": "tip", "comment": "..." }
```
`kind`: `bits`, `tip`, `donation`

### `subscription`
```json
{ "username": "...", "tier": 1, "is_resub": false, "months": null, "message": "..." }
```
`tier`: 1, 2, or 3

### `gift_sub`
```json
{ "gifter": "...", "recipients": ["..."], "tier": 1, "count": 1 }
```
`gifter` is `null` for anonymous gifts.

### `raid/incoming`
```json
{ "from_channel": "...", "viewer_count": 42 }
```

### `raid/outgoing`
Not currently emitted by ongwatch.

### `hype_train`
```json
{ "kind": "begin", "level": 1, "total": 1000 }
```
`kind`: `begin` or `end`

### `song_request`
```json
{ "title": "...", "requester": "..." }
```

### `raffle_win`
```json
{ "winner": "..." }
```

### `stream/status`
```json
{ "state": "online" }
```
`state`: `online` or `offline`

### `queue/head`
Not currently emitted by ongwatch.

### `stream/viewers`, `stream/mode`
Not currently emitted by ongwatch.

## ongwatch.toml configuration

```toml
[outputs.mqtt.production]
host            = "localhost"
port            = 1883
channel         = "jonathanong"
topic_prefix    = ""            # prepended to {channel}/... if set
client_id       = ""            # default: "ongwatch-{channel}"
username        = ""
password        = ""
tls             = false
qos_events      = 1
qos_state       = 1
qos_heartbeat   = 0
on_error        = "queue"
queue_max_size  = 500
queue_overflow  = "drop_oldest"
```
