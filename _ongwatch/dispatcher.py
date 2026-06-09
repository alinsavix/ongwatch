from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any

from .events import OngwatchEvent
from .outputs import Output, SendStatus

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Circuit state
# ---------------------------------------------------------------------------

@dataclass
class _Closed:
    pass


@dataclass
class _Open:
    retry_at: datetime


# ---------------------------------------------------------------------------
# Per-output config and stats
# ---------------------------------------------------------------------------


class OnErrorPolicy(StrEnum):
    QUEUE = "queue"
    DROP = "drop"


class QueueOverflowPolicy(StrEnum):
    DROP_OLDEST = "drop_oldest"
    DROP_NEWEST = "drop_newest"
    CIRCUIT_BREAK = "circuit_break"

@dataclass
class OutputConfig:
    on_error: OnErrorPolicy = OnErrorPolicy.QUEUE
    queue_max_size: int = 0               # 0 = unbounded (only for "queue" mode)
    queue_overflow: QueueOverflowPolicy = QueueOverflowPolicy.DROP_OLDEST
    circuit_break_cooldown: float = 300.0
    circuit_break_flush_queue: bool = False
    max_retries: int = 3  # caps backoff growth (2**n s); does not drop events

    def __post_init__(self) -> None:
        try:
            self.on_error = OnErrorPolicy(self.on_error)
        except ValueError as exc:
            raise ValueError("OutputConfig.on_error must be 'queue' or 'drop'") from exc
        try:
            self.queue_overflow = QueueOverflowPolicy(self.queue_overflow)
        except ValueError as exc:
            raise ValueError(
                "OutputConfig.queue_overflow must be "
                "'drop_oldest', 'drop_newest', or 'circuit_break'"
            ) from exc
        if self.queue_max_size < 0:
            raise ValueError("OutputConfig.queue_max_size must be >= 0")
        if self.circuit_break_cooldown < 0:
            raise ValueError("OutputConfig.circuit_break_cooldown must be >= 0")
        if self.max_retries < 0:
            raise ValueError("OutputConfig.max_retries must be >= 0")


@dataclass
class OutputStats:
    received: int = 0
    handled: int = 0
    rejected: int = 0
    dropped: int = 0
    errored: int = 0
    transient_retries: int = 0
    circuit_trips: int = 0
    heartbeats_ok: int = 0
    heartbeats_failed: int = 0
    last_handled_at: datetime | None = None
    last_error_at: datetime | None = None
    last_heartbeat_at: datetime | None = None


# ---------------------------------------------------------------------------
# Per-output runtime state
# ---------------------------------------------------------------------------

class _OutputState:
    def __init__(self, name: str, output: Output, config: OutputConfig) -> None:
        self.name = name
        self.output = output
        self.config = config
        self.stats = OutputStats()
        self.circuit: _Closed | _Open = _Closed()
        self._notify: asyncio.Event = asyncio.Event()
        self._worker_task: asyncio.Task[None] | None = None
        self._retry_counts: dict[int, int] = {}  # id(event) -> attempt count
        self._draining: bool = False
        # Heartbeat health: None = not yet probed, True = online, False = down.
        # Drives the online/offline/back-online transition logging.
        self._online: bool | None = None
        self._queue: deque[OngwatchEvent] | None = (
            deque() if config.on_error == OnErrorPolicy.QUEUE else None
        )

    @property
    def queue_depth(self) -> int:
        return len(self._queue) if self._queue is not None else 0

    def _at_capacity(self) -> bool:
        if self._queue is None or self.config.queue_max_size == 0:
            return False
        return len(self._queue) >= self.config.queue_max_size

    def _trip_circuit(self) -> None:
        retry_at = datetime.now(tz=timezone.utc) + timedelta(
            seconds=self.config.circuit_break_cooldown
        )
        self.circuit = _Open(retry_at=retry_at)
        self.stats.circuit_trips += 1
        log.warning(
            "Circuit breaker tripped for output %r, probe after %s",
            self.name, retry_at.isoformat(),
        )
        if self.config.circuit_break_flush_queue and self._queue:
            dropped = len(self._queue)
            self._queue.clear()
            self.stats.dropped += dropped
            log.warning(
                "Flushed %d queued events on circuit break for output %r",
                dropped, self.name,
            )

    def enqueue(self, event: OngwatchEvent) -> None:
        """Append event to the back of the queue, applying overflow policy if full."""
        assert self._queue is not None
        if not self._at_capacity():
            self._queue.append(event)
            self._notify.set()
            return

        policy = self.config.queue_overflow
        if policy == QueueOverflowPolicy.DROP_OLDEST:
            self._queue.popleft()
            self.stats.dropped += 1
            self._queue.append(event)
            self._notify.set()
        elif policy == QueueOverflowPolicy.DROP_NEWEST:
            self.stats.dropped += 1
        elif policy == QueueOverflowPolicy.CIRCUIT_BREAK:
            self._trip_circuit()


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

class Dispatcher:
    def __init__(
        self,
        outputs: list[tuple[str, Output, OutputConfig]],
        heartbeat_interval: int = 60,
    ) -> None:
        self._states = [_OutputState(name, out, cfg) for name, out, cfg in outputs]
        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._accepting = True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def emit(self, event: OngwatchEvent) -> None:
        """Synchronous. Called by backends to dispatch a normalized event."""
        if not self._accepting:
            return
        for state in self._states:
            state.stats.received += 1
            if isinstance(state.circuit, _Open):
                state.stats.dropped += 1
                log.debug("Circuit open for %r, dropping event", state.name)
                continue
            if state.config.on_error == OnErrorPolicy.DROP:
                asyncio.create_task(self._fire_and_forget(state, event))
            else:
                state.enqueue(event)

    async def start(self) -> None:
        """Start per-output worker tasks and the heartbeat task."""
        for state in self._states:
            if state.config.on_error == OnErrorPolicy.QUEUE:
                state._worker_task = asyncio.create_task(
                    self._worker(state), name=f"worker:{state.name}"
                )
        self._heartbeat_task = asyncio.create_task(
            self._heartbeat(), name="dispatcher:heartbeat"
        )

    async def drain(self, timeout: float = 30.0) -> None:
        """Stop accepting new events and wait for queues to empty, up to timeout."""
        self._accepting = False
        for state in self._states:
            state._draining = True
            state._notify.set()  # wake worker so it sees the draining flag

        worker_tasks = [
            s._worker_task for s in self._states
            if s._worker_task is not None and not s._worker_task.done()
        ]
        if not worker_tasks:
            return

        try:
            await asyncio.wait_for(
                asyncio.gather(*worker_tasks, return_exceptions=True),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            remaining = sum(s.queue_depth for s in self._states)
            log.warning(
                "Drain timed out after %.1fs; approximately %d queued events dropped",
                timeout, remaining,
            )
            for task in worker_tasks:
                task.cancel()

    async def stop(self) -> None:
        """Cancel the heartbeat and any still-running worker tasks."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        for state in self._states:
            if state._worker_task and not state._worker_task.done():
                state._worker_task.cancel()

    def stats(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for state in self._states:
            s = state.stats
            result[state.name] = {
                "received": s.received,
                "handled": s.handled,
                "rejected": s.rejected,
                "dropped": s.dropped,
                "errored": s.errored,
                "transient_retries": s.transient_retries,
                "queue_depth": state.queue_depth,
                "circuit_trips": s.circuit_trips,
                "heartbeats_ok": s.heartbeats_ok,
                "heartbeats_failed": s.heartbeats_failed,
                "last_handled_at": s.last_handled_at,
                "last_error_at": s.last_error_at,
                "last_heartbeat_at": s.last_heartbeat_at,
                "circuit_state": "open" if isinstance(state.circuit, _Open) else "closed",
            }
        return result

    # ------------------------------------------------------------------
    # Internal tasks
    # ------------------------------------------------------------------

    async def _fire_and_forget(self, state: _OutputState, event: OngwatchEvent) -> None:
        """Send one event for an on_error=drop output; no retry."""
        try:
            result = await state.output.send(event)
        except Exception:
            log.exception("Output %r raised unexpectedly during send", state.name)
            result = SendStatus.ERROR

        now = datetime.now(tz=timezone.utc)
        if result == SendStatus.HANDLED:
            state.stats.handled += 1
            state.stats.last_handled_at = now
        elif result == SendStatus.REJECTED:
            state.stats.rejected += 1
        else:
            # TRANSIENT or ERROR — no retry in drop mode
            state.stats.dropped += 1
            if result == SendStatus.ERROR:
                state.stats.errored += 1
                state.stats.last_error_at = now
                log.error(
                    "Output %r returned ERROR (on_error=drop, not retrying)", state.name
                )

    async def _worker(self, state: _OutputState) -> None:
        """Per-output worker: dequeue events and call output.send()."""
        queue = state._queue
        assert queue is not None

        while True:
            while queue:
                event = queue.popleft()
                retry_count = state._retry_counts.get(id(event), 0)

                try:
                    result = await state.output.send(event)
                except Exception:
                    log.exception("Output %r raised unexpectedly during send", state.name)
                    result = SendStatus.ERROR

                now = datetime.now(tz=timezone.utc)

                if result == SendStatus.HANDLED:
                    state.stats.handled += 1
                    state.stats.last_handled_at = now
                    state._retry_counts.pop(id(event), None)

                elif result == SendStatus.REJECTED:
                    state.stats.rejected += 1
                    state._retry_counts.pop(id(event), None)

                elif result == SendStatus.TRANSIENT:
                    # TRANSIENT means "couldn't deliver right now", not that
                    # the event is bad. With on_error=queue we never drop it
                    # for failing — we re-queue at the front and back off.
                    # queue_overflow (applied in enqueue() when queue_max_size
                    # is exceeded) is the only thing that drops events;
                    # max_retries only caps how high the backoff escalates.
                    state.stats.transient_retries += 1
                    state._retry_counts[id(event)] = retry_count + 1
                    backoff = float(2 ** min(retry_count, state.config.max_retries))
                    log.debug(
                        "Output %r TRANSIENT, re-queue and retry in %.1fs (attempt %d)",
                        state.name, backoff, retry_count + 1,
                    )
                    await asyncio.sleep(backoff)
                    queue.appendleft(event)

                elif result == SendStatus.ERROR:
                    state._retry_counts.pop(id(event), None)
                    state.stats.errored += 1
                    state.stats.last_error_at = now
                    log.error("Output %r returned ERROR, dropping event", state.name)

            if state._draining:
                return

            # Wait for the next event, being careful not to miss a wakeup
            # that arrived between exhausting the queue and clearing the flag.
            state._notify.clear()
            if queue:  # event arrived between while-check and clear
                continue
            await state._notify.wait()

    async def _heartbeat(self) -> None:
        """Periodic task: probe all outputs and drive circuit-breaker recovery."""
        # Probe immediately on startup so each output's online/offline status
        # is logged promptly, then settle into the configured interval.
        first = True
        while True:
            if first:
                first = False
            else:
                await asyncio.sleep(self._heartbeat_interval)
            now = datetime.now(tz=timezone.utc)
            for state in self._states:
                if isinstance(state.circuit, _Open):
                    if now >= state.circuit.retry_at:
                        try:
                            await state.output.heartbeat()
                            state.circuit = _Closed()
                            state.stats.heartbeats_ok += 1
                            state.stats.last_heartbeat_at = now
                            state._online = True
                            log.info("Output %r circuit recovered after probe", state.name)
                            # Re-start worker if it exited during the open period
                            if (
                                state.config.on_error == OnErrorPolicy.QUEUE
                                and (state._worker_task is None or state._worker_task.done())
                            ):
                                state._draining = False
                                state._worker_task = asyncio.create_task(
                                    self._worker(state), name=f"worker:{state.name}"
                                )
                        except Exception:
                            new_retry = now + timedelta(
                                seconds=state.config.circuit_break_cooldown
                            )
                            state.circuit = _Open(retry_at=new_retry)
                            state.stats.heartbeats_failed += 1
                            state._online = False
                            log.warning(
                                "Output %r probe failed, next attempt after %s",
                                state.name, new_retry.isoformat(),
                            )
                    else:
                        log.debug(
                            "Output %r circuit open, probe scheduled after %s",
                            state.name, state.circuit.retry_at.isoformat(),
                        )
                else:
                    try:
                        await state.output.heartbeat()
                        state.stats.heartbeats_ok += 1
                        state.stats.last_heartbeat_at = now
                        self._record_online(state)
                    except Exception as exc:
                        state.stats.heartbeats_failed += 1
                        self._record_offline(state, exc)

    def _record_online(self, state: _OutputState) -> None:
        """Log a transition to a healthy output; no-op if already online."""
        if state._online is None:
            log.info("Output %r is online", state.name)
        elif state._online is False:
            log.info("Output %r is back online", state.name)
        state._online = True

    def _record_offline(self, state: _OutputState, exc: BaseException) -> None:
        """Log a transition to an unhealthy output, and keep warning while down."""
        if state._online is False:
            log.warning("Output %r still offline: %s", state.name, exc)
        else:
            log.warning("Output %r is offline: %s", state.name, exc)
        state._online = False
