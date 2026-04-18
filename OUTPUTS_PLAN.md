# Plan: Modular Output System for ongwatch

## Context

ongwatch currently routes all events from backends (Twitch, StreamElements, Streamlabs) directly to stdout via hardcoded `printsupport()` and `out()` calls in `_ongwatch/util.py`. This is tightly coupled and makes it impossible to support multiple simultaneous outputs, add new output types, or isolate output failures. The goal is a pluggable output system where normalized events flow from backends through a central dispatcher to independently-configured outputs (bumplog file, MQTT, SQLite, console), with each output isolated so a failure in one cannot affect others.

**Testability note:** The design should keep future testing in mind throughout. Specifically: each backend's raw-to-normalized mapping should be a separable function (not inlined in event handlers) so it can be tested without a live connection; the dispatcher should be testable via a `MockOutput` in `_ongwatch/outputs/testing.py`; event construction should be straightforward enough to support test fixtures; and the async surface suggests `pytest-asyncio` when tests are written.

---

## 1. Normalized Event Types

**New file:** `_ongwatch/events.py`

All events share a base dataclass:

```python
@dataclass
class OngwatchEvent:
    timestamp: datetime
    backend: str      # "twitch", "streamelements", "streamlabs"
    raw: Any          # original backend payload (TwitchIO model, dict, etc.)
```

Subtypes are divided into **currently emitted** (backends already generate these) and **defined/reserved** (types are defined now so outputs can handle them; backends don't yet subscribe to these Twitch EventSub events).

### Currently emitted

| Class | Fields | Sources |
|---|---|---|
| `CashSupportEvent` | `username`, `amount: float`, `kind: str` ("bits"/"tip"/"donation"), `comment: str \| None` | bits (Twitch), tip (SE), donation (SL) |
| `SubscriptionEvent` | `username`, `tier: int` (1/2/3), `is_resub: bool`, `months: int \| None`, `message: str \| None` | Twitch sub/resub/prime upgrade |
| `GiftSubEvent` | `gifter: str \| None` (None=anonymous), `recipients: list[str]`, `tier: int`, `count: int` | Twitch gift/community gift/pay-it-forward |
| `RaidEvent` | `from_channel: str`, `viewer_count: int` | Twitch raid |
| `StreamStateEvent` | `state: str` ("online"/"offline") | Twitch stream.online/offline |
| `HypeTrainEvent` | `kind: str` ("begin"/"end"), `level: int`, `total: int` | Twitch hype_train |
| `SongRequestEvent` | `title: str`, `requester: str \| None` | Nightbot chat parsing (Twitch-specific) |

### Defined/reserved (backends not yet subscribed)

| Class | Fields | Twitch EventSub source |
|---|---|---|
| `FollowEvent` | `username`, `followed_at: datetime` | `channel.follow` |
| `ChannelPointRedemptionEvent` | `username`, `reward_title: str`, `reward_cost: int`, `user_input: str \| None`, `status: str` | `channel.channel_points_custom_reward_redemption.add` |
| `PollEvent` | `kind: str` ("begin"/"progress"/"end"), `title: str`, `choices: list[dict]` ({title, votes}), `winning_choice: str \| None` | `channel.poll.*` |
| `PredictionEvent` | `kind: str` ("begin"/"progress"/"locked"/"end"), `title: str`, `outcomes: list[dict]` ({title, users, channel_points}), `winning_outcome: str \| None` | `channel.prediction.*` |
| `CharityDonationEvent` | `username`, `amount: float`, `currency: str`, `campaign_name: str` | `channel.charity_campaign.donate` |
| `GoalEvent` | `kind: str` ("begin"/"progress"/"end"), `goal_type: str`, `current: int`, `target: int` | `channel.goal.*` |
| `ShoutoutEvent` | `kind: str` ("sent"/"received"), `channel: str`, `viewer_count: int \| None` | `channel.shoutout.*` |

Each backend module gains a private mapping layer — a function or methods that converts raw backend event objects/dicts into the appropriate `OngwatchEvent` subclass. The `raw` field preserves the original payload for outputs that want backend-specific detail.

---

## 2. Output Protocol

**New file:** `_ongwatch/outputs/__init__.py`

```python
class Output(Protocol):
    async def start(self) -> None: ...      # connect, open file, etc.
    async def stop(self) -> None: ...       # flush, disconnect, close
    async def send(self, event: OngwatchEvent) -> SendStatus: ...
    async def heartbeat(self) -> None: ...  # verify health; raises on failure
```

### SendStatus

`send()` returns a `SendStatus` enum rather than raising exceptions for control flow:

```python
class SendStatus(Enum):
    HANDLED   = "handled"    # delivered successfully
    REJECTED  = "rejected"   # wrong type for this output, intentionally ignored
    TRANSIENT = "transient"  # couldn't deliver right now, please retry
    ERROR     = "error"      # something is wrong, do not retry this event
```

If `send()` raises an uncaught exception (output bug), the dispatcher catches it and treats it as `ERROR`.

### Unknown / unhandled event types

The dispatcher sends **every event to every output** — no filtering at the dispatch layer. Each output's `send()` is responsible for ignoring event types it doesn't handle. The recommended pattern is an early return:

```python
async def send(self, event: OngwatchEvent) -> SendStatus:
    if not isinstance(event, (CashSupportEvent, SubscriptionEvent, GiftSubEvent)):
        return SendStatus.REJECTED
    # ... handle it
    return SendStatus.HANDLED
```

This keeps the dispatcher simple and ensures outputs remain forward-compatible: a new event type added to `events.py` is silently ignored by existing outputs until they opt in.

`heartbeat()` is a required protocol method, **not** an event subtype. It bypasses the per-output queue so it remains reachable even during queue pressure or circuit-break state. Each output decides what "healthy" means:

- bumplog: write a `# heartbeat <ts>` comment line  
- MQTT: publish to `ongwatch/heartbeat`  
- SQLite: `INSERT OR REPLACE INTO _heartbeat (ts) VALUES (?)`  
- console: no-op (or quiet log)

**Output registry** mirrors the backend registry: `OUTPUT_LIST`, `get_output(name)` via `importlib.import_module`.

---

## 3. Dispatcher

**New file:** `_ongwatch/dispatcher.py`

The dispatcher is instantiated once in `ongwatch.py` and injected into every backend's `start()` call.

### Per-output infrastructure (one set per registered output)

- `collections.deque(maxlen=queue_max_size or None)` — used instead of `asyncio.Queue` to support front-insertion for `TRANSIENT` re-enqueuing; 0 = unbounded
- Worker task: see behavior below
- Circuit state: `Closed` | `Open(retry_at: datetime)`
- Stats counters: `received`, `handled`, `rejected`, `dropped`, `errored`, `transient_retries`, `queue_depth` (live), `circuit_trips`, `heartbeats_ok`, `heartbeats_failed`, `last_handled_at`, `last_error_at`, `last_heartbeat_at`

### `emit(event: OngwatchEvent)`

Called by backends. For each registered output:

- **Closed**: enqueue event at back; increment `received`; if queue full, apply `queue_overflow` policy (increment `dropped` on drop)
- **Open**: drop event immediately (fast-fail); increment `dropped`; log at debug level

### Worker task behavior

For each event dequeued from the front:

| `send()` result | Action |
|---|---|
| `HANDLED` | Increment `handled`; reset retry count for this event |
| `REJECTED` | Increment `rejected`; advance to next event |
| `TRANSIENT` | Increment `transient_retries`; if retry count < `max_retries`: re-enqueue **at front**, apply exponential backoff (starting ~1s); else treat as `ERROR` |
| `ERROR` | Increment `errored`; log at error level; drop event; advance to next |
| Uncaught exception | Treat as `ERROR` |

Per-event retry count is tracked in a small dict keyed by event identity. Entries are removed on `HANDLED`, `REJECTED`, or final `ERROR`.

### Queue overflow policies

| `queue_overflow` | Behavior when `queue_max_size` is reached |
|---|---|
| `drop_oldest` | Discard the oldest queued event, enqueue new one |
| `drop_newest` | Discard the new event (keep backlog intact) |
| `circuit_break` | Transition output to Open; optionally flush queue; start `circuit_break_cooldown` timer; log warning |

### Heartbeat task

Periodic asyncio task (global `heartbeat_interval`, default 60s). For each output:

- **Closed**: call `output.heartbeat()`; on failure, log warning (does not trip circuit by itself — that's queue-driven)
- **Open**: if `retry_at` has passed, call `output.heartbeat()` as probe; success → transition to Closed and log recovery; failure → reset `retry_at = now + cooldown`, log

### Circuit-break config (per output, in credentials.toml)

```toml
[outputs.mqtt.production]
host = "localhost"
port = 1883
on_error = "queue"
queue_max_size = 500
queue_overflow = "circuit_break"
circuit_break_cooldown = 300        # seconds before probe attempt
circuit_break_flush_queue = true    # discard buffered events when tripping
max_retries = 3                     # TRANSIENT retry attempts before treating as ERROR (default: 3)
```

`on_error = "drop"` is equivalent to `queue_max_size = 0` — no queue, events always dropped on failure. Both spellings should be accepted.

Stats for all outputs are accessible on the dispatcher (e.g. `dispatcher.stats()`) and can be surfaced via logging, a signal handler, or a future stats output. How stats are *exposed* is out of scope for this plan.

---

## 4. Backend Changes

**Modified:** `_ongwatch/backends/twitch.py`, `streamelements.py`, `streamlabs.py`

Each backend's `start()` signature gains a `dispatcher` parameter:

```python
async def start(
    args: argparse.Namespace,
    creds: dict | None,
    logger: logging.Logger,
    dispatcher: Dispatcher,
) -> None
```

All `printsupport()`, `out()`, and `printextra()` calls are replaced with `await dispatcher.emit(SomeEvent(...))`.

Each backend gains a private mapping layer of pure functions (e.g. `_map_bits_event(payload) -> CashSupportEvent`) that convert raw backend types to normalized events. These are separate from the event handlers to support future unit testing without a live connection.

`util.printsupport()` and `util.printextra()` are deleted once no backend calls them.

---

## 5. Known Output Implementations

Build in this order; each proves the protocol before the next.

### 5a. BumpLogOutput (reference implementation)
**New file:** `_ongwatch/outputs/bumplog.py`

- Writes to a configurable `path` (file path string; `-` or `stdout` → sys.stdout for interactive use)
- Replicates current `printsupport()` tab-separated format for cash/sub events
- `heartbeat()`: appends `# heartbeat <iso-timestamp>\n`
- On failure (disk full, etc.): `drop` is the sensible default; `queue` supported but of limited value

### 5b. ConsoleOutput
**New file:** `_ongwatch/outputs/console.py`

- Lightweight wrapper around sys.stdout for interactive terminal watching
- Formats events human-readably (could share formatter with bumplog)
- `heartbeat()`: no-op
- No queueing concerns (writes are synchronous and fast)

### 5c. MQTTOutput
**New file:** `_ongwatch/outputs/mqtt.py`

- Uses `aiomqtt` (or `asyncio-mqtt`)
- Reconnects automatically; heartbeat publishes to a dedicated heartbeat topic
- Typical config: `queue_overflow = "circuit_break"`, stale events not worth delivering after reconnect

> **Topic hierarchy is a separate design task.** The MQTT topic structure is a public interface — other tools will subscribe to these topics — and some messages will need the retained flag set, others won't. This needs careful design before the MQTT output is implemented. Key questions to answer in that task: topic naming scheme, which event types get retained messages (e.g. stream state probably yes; individual cheers probably no), payload format (JSON?), and versioning strategy. Do not implement `mqtt.py` until the topic hierarchy is designed and documented.

### 5d. SQLiteOutput
**New file:** `_ongwatch/outputs/sqlite.py`

- Uses `aiosqlite`
- One table per event type + a `_heartbeat` table
- Stores both normalized fields and JSON-serialized `raw` payload
- Typical config: `queue_max_size = 0` (unbounded — don't lose records)

---

## 6. ongwatch.py Changes

**Modified:** `ongwatch.py`

In `async_main()`:
1. Read `[outputs.*]` sections from `credentials.toml`, build list of enabled outputs
2. Call `output.start()` for each
3. Instantiate `Dispatcher(outputs, heartbeat_interval=...)`
4. Start dispatcher's heartbeat task
5. Pass `dispatcher` into each backend `start()` call
6. On shutdown: cancel backends → flush dispatcher queues → call `output.stop()` for each

---

## 7. Configuration (credentials.toml)

Outputs follow the existing `[section.name.environment]` pattern already stubbed in the file:

```toml
[outputs.bumplog.production]
path = "/path/to/bump.log"
on_error = "queue"
queue_max_size = 100
queue_overflow = "drop_oldest"
# max_retries = 3  (default)

[outputs.console.production]
# no credentials needed; max_retries not meaningful (writes are local/fast)

[outputs.mqtt.production]
host = "mqtt.example.com"
port = 1883
on_error = "queue"
queue_max_size = 500
queue_overflow = "circuit_break"
circuit_break_cooldown = 300
circuit_break_flush_queue = true
max_retries = 5   # extra retries for network transport

[outputs.sqlite.production]
path = "/var/log/ongwatch.db"
on_error = "queue"
queue_max_size = 0   # unbounded — don't lose records
queue_overflow = "drop_oldest"
max_retries = 3
```

---

## Critical Files

| File | Status | Role |
|---|---|---|
| `_ongwatch/events.py` | New | Normalized event dataclasses |
| `_ongwatch/dispatcher.py` | New | Dispatcher, per-output queues, circuit breaker, heartbeat scheduler |
| `_ongwatch/outputs/__init__.py` | New | Output protocol + registry |
| `_ongwatch/outputs/bumplog.py` | New | Reference output implementation |
| `_ongwatch/outputs/console.py` | New | Interactive terminal output |
| `_ongwatch/outputs/mqtt.py` | New | MQTT output (pending topic hierarchy design) |
| `_ongwatch/outputs/sqlite.py` | New | SQLite output |
| `_ongwatch/outputs/testing.py` | New | MockOutput for future test use |
| `_ongwatch/backends/twitch.py` | Modified | Replace printsupport() with dispatcher.emit(); extract mapping functions |
| `_ongwatch/backends/streamelements.py` | Modified | Same |
| `_ongwatch/backends/streamlabs.py` | Modified | Same |
| `ongwatch.py` | Modified | Initialize outputs, create dispatcher, pass to backends |
| `credentials.toml` | Modified | Add [outputs.*] sections |
| `_ongwatch/util.py` | Modified | Remove printsupport(), printextra() once unused |

---

## Implementation Order

1. `_ongwatch/events.py` — event types (no deps, can be reviewed standalone)
2. `_ongwatch/outputs/__init__.py` — Output protocol + registry
3. `_ongwatch/dispatcher.py` — dispatcher with queue/circuit logic
4. `_ongwatch/outputs/bumplog.py` — reference implementation
5. Wire up: modify `ongwatch.py` + all three backends; delete old util functions
6. Test end-to-end with bumplog only
7. Add console, MQTT, SQLite outputs as follow-on

---

## Verification

1. Run with `[outputs.bumplog.production]` configured; generate a test event (e.g. mock bits cheer); verify tab-separated line appears in configured file.
2. Configure bumplog `path = "-"`; verify output appears on stdout.
3. Configure a non-existent MQTT broker with `queue_max_size = 5, queue_overflow = "circuit_break"`; send 6 events; verify circuit trips and log shows warning.
4. Restore MQTT broker; wait for `circuit_break_cooldown`; verify heartbeat probe fires and circuit closes.
5. Let stream sit idle (no events); verify heartbeat lines appear in bumplog at configured interval.
6. Configure two outputs (bumplog + a bad MQTT); verify bumplog continues receiving events while MQTT circuit-breaks.
7. Manually verify that all three backends still emit events correctly end-to-end after the `printsupport()` calls are removed.
