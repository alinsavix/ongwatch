from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
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

@dataclass
class OutputConfig:
    on_error: str = "queue"               # "queue" | "drop"
    queue_max_size: int = 0               # 0 = unbounded (only for "queue" mode)
    queue_overflow: str = "drop_oldest"   # "drop_oldest" | "drop_newest" | "circuit_break"
    circuit_break_cooldown: float = 300.0
    circuit_break_flush_queue: bool = False
    max_retries: int = 3


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
        self._queue: deque[OngwatchEvent] | None = (
            deque() if config.on_error == "queue" else None
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
        if policy == "drop_oldest":
            self._queue.popleft()
            self.stats.dropped += 1
            self._queue.append(event)
            self._notify.set()
        elif policy == "drop_newest":
            self.stats.dropped += 1
        elif policy == "circuit_break":
            self._trip_circuit()
        else:
            log.warning(
                "Unknown queue_overflow policy %r for output %r, dropping event",
                policy, self.name,
            )
            self.stats.dropped += 1


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

class Dispatcher:
    def __init__(
        self,
        outputs: list[tuple[str, Output, OutputConfig]],
        heartbeat_interval: float = 60.0,
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
            if state.config.on_error == "drop":
                asyncio.create_task(self._fire_and_forget(state, event))
            else:
                state.enqueue(event)

    async def start(self) -> None:
        """Start per-output worker tasks and the heartbeat task."""
        for state in self._states:
            if state.config.on_error == "queue":
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
                    state.stats.transient_retries += 1
                    if retry_count < state.config.max_retries:
                        state._retry_counts[id(event)] = retry_count + 1
                        backoff = float(2 ** retry_count)  # 1, 2, 4, 8 ... seconds
                        log.debug(
                            "Output %r TRANSIENT, retry %d/%d in %.1fs",
                            state.name, retry_count + 1, state.config.max_retries, backoff,
                        )
                        await asyncio.sleep(backoff)
                        queue.appendleft(event)
                    else:
                        state._retry_counts.pop(id(event), None)
                        state.stats.errored += 1
                        state.stats.last_error_at = now
                        state.stats.dropped += 1
                        log.error(
                            "Output %r TRANSIENT exhausted %d retries, dropping event",
                            state.name, state.config.max_retries,
                        )

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
        while True:
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
                            log.info("Output %r circuit recovered after probe", state.name)
                            # Re-start worker if it exited during the open period
                            if (
                                state.config.on_error == "queue"
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
                    except Exception:
                        state.stats.heartbeats_failed += 1
                        log.warning("Output %r heartbeat failed", state.name)
