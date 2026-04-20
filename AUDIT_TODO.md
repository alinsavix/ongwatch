# Audit Findings

Numbered for easy reference. Grouped by priority.

---

## P0 — Blockers (app doesn't work correctly today)

**#1 — Twitch auth is broken**
`_ongwatch/backends/auth/twitch.py:53,58`
`oauth.device_code_flow()`, `oauth.device_code_authorization()`, and
`twitchio.DeviceCodeFlowException` don't exist on TwitchIO 3.x. The `--auth
twitch` command crashes immediately with AttributeError.  [DCF tokens not supported until next major release of TwitchIO, we're ok with this being broken until then --A]

**#2 — No token refresh**
`_ongwatch/backends/twitch.py:231-234`
`save_tokens=False` and no refresh callback means the Twitch connection
silently dies after ~1 hour when the access token expires. Most critical
runtime issue for a long-running process.  [We're using DCF tokens, which don't need to refresh, so this is a false alarm --A]

**#3 — App exits on any backend failure**
`ongwatch.py:91-98`
`asyncio.wait(..., return_when=FIRST_COMPLETED)` means if any backend task
dies (e.g. StreamElements network hiccup), the whole process exits, taking
all other backends with it. No per-backend restart logic.

---

## P1 — Serious reliability/correctness issues

**#4 — `sio.wait()` hangs forever**
`_ongwatch/backends/streamelements.py:88`, `_ongwatch/backends/streamlabs.py:84`
If socket.io gives up reconnecting, `await sio.wait()` never returns. The
task becomes unkillable. Needs a timeout or cancellation-aware wrapper.

**#5 — No graceful shutdown timeout**
`ongwatch.py:105`
`await asyncio.gather(..., return_exceptions=True)` waits indefinitely for
tasks to finish. If a task ignores cancellation, the process never exits.

**#6 — `None` passed as `str` in event handlers**
`_ongwatch/backends/twitch.py:140,162,189,195,213,232`
`payload.chatter.display_name`, `payload.user_name`, `payload.from_user`,
etc. are all `str | None` but are passed to functions expecting `str` or used
as dict keys. Will crash at runtime if Twitch sends a partial payload.

**#7 — Token/credentials loading has no error handling**
`_ongwatch/util.py:62-64`
`get_token()` does a bare `open()` + `json.load()` — `FileNotFoundError` and
`json.JSONDecodeError` propagate as raw tracebacks. `get_credentials()` also
doesn't catch `FileNotFoundError` or `toml.TOMLDecodeError` for missing or
malformed files.

---

## P2 — Architecture issues that will block future improvements

**#8 — Custom print-based logging bypasses `logging` module**
`_ongwatch/util.py:15-59`
`out()`, `log()`, `printsupport()`, `printextra()` all print directly to
stdout/stderr. Cannot be suppressed, routed, or level-controlled. When a
message bus output layer is added, events need to flow through `logging` or a
proper event pipeline so they can be routed anywhere. (See also: FIXME comment
in util.py.)

**#9 — No `Backend` protocol**
`_ongwatch/backends/__init__.py:7-18`
Backends are validated with `"auth" in dir(module)` string checks. Without a
formal `Protocol` class, adding new interface methods (health checks, graceful
stop, etc.) requires touching every backend with no compile-time validation.

**#10 — Hardcoded backend list**
`_ongwatch/backends/__init__.py:13`
`BACKEND_LIST = ["twitch", "streamelements", "streamlabs"]`. Adding a backend
requires editing this file. Should be auto-discovered from the `backends/`
directory or driven from config.

**#11 — Backends directly call `printsupport()` — no output abstraction**
All backend files.
Events go: backend → `printsupport()` → stdout. No abstraction for "what to
do with an event." Adding the message bus will require threading an output
handler through every backend rather than just swapping the sink. An event
callback or async queue pattern would decouple this cleanly now.

**#12 — No event normalization layer**
Twitch, StreamElements, and Streamlabs use different field names and
structures for semantically equivalent events (e.g. "tip" vs "donation").
There is no shared event model. Consumers of the message bus will need to
handle events from multiple sources uniformly.

---

## P3 — Code quality / type safety

**#13 — 17 mypy errors despite strict config**
`pyproject.toml` declares strict mypy settings that the codebase does not pass.
The strict settings are aspirational; they should either be enforced (fix the
errors) or relaxed to match reality.

**#14 — All socket.io event handlers are untyped**
`_ongwatch/backends/streamelements.py:24,30,33,38,41,44`
`_ongwatch/backends/streamlabs.py:25,28,36,39,42`
Noted in FIXMEs. Means mypy gives up type-checking the entire body of those
methods.

**#15 — Bare dict key access on event payloads**
`_ongwatch/backends/streamelements.py:45`, `_ongwatch/backends/streamlabs.py:43`
`event['type']`, `event['data']`, etc. will crash with `KeyError` if the
upstream API changes its payload shape. Use `.get()` with validation or
define typed payload models.

**#16 — `python-socketio` pinned to exact version**
`pyproject.toml:24`
`==4.6.1` is unnecessarily strict. `>=4.6.1,<5.0.0` would allow patch
updates without breaking the major version contract. [we need this to be able to get the specific protocol version we need, sadly --A]

**#17 — `requires-python` has unusual patch-level lower bound**
`pyproject.toml:20`
`>=3.13.10,<3.14` will reject users on 3.13.9. Unless there is a specific
bug fix required at that exact patch level, `>=3.13,<3.14` is more
conventional.

---

## P4 — Observability / operations

**#18 — No structured logging**
Plain string log messages with no key-value pairs. Hard to grep or aggregate
when debugging live issues. Consider adding context (backend name, event type,
user) as structured fields.

**#19 — No credential validation at startup**
The app starts all backends before discovering a missing key in
`credentials.conf`. Should validate all required keys exist for enabled
backends before entering the async event loop.

**#20 — No health checks**
No way to externally probe whether backends are connected and functional.

**#21 — No test suite**
Zero test files. Utility functions (`get_credentials`, `get_token`, Nightbot
message parsing) are pure or near-pure and could be unit tested right now
without mocking anything.
