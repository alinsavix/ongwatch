"""
MockOutput — a test double for the Output protocol.

Usage in tests::

    from _ongwatch.outputs.testing import MockOutput
    from _ongwatch.outputs import SendStatus

    mock = MockOutput()                          # defaults: always HANDLED
    mock = MockOutput(default_status=SendStatus.TRANSIENT)
    mock = MockOutput(responses={CashSupportEvent: SendStatus.REJECTED})

    dispatcher = Dispatcher([("mock", mock, OutputConfig())], heartbeat_interval=9999)
    await mock.start()
    await dispatcher.start()

    dispatcher.emit(some_event)
    await dispatcher.drain(timeout=1)

    assert len(mock.received) == 1
    assert mock.heartbeat_count == 0
"""
from __future__ import annotations

from typing import Any

from ..events import OngwatchEvent
from . import SendStatus


class MockOutput:
    """
    Captures every event delivered via send() into ``received``.

    Parameters
    ----------
    default_status:
        ``SendStatus`` returned for any event type not in ``responses``.
        Defaults to ``HANDLED``.
    responses:
        Optional mapping of event *class* → ``SendStatus``.  When an event
        whose type matches a key is delivered, the mapped status is returned
        instead of ``default_status``.
    raise_on_send:
        If ``True``, ``send()`` raises ``RuntimeError`` unconditionally
        (simulates a buggy/crashing output so the dispatcher's exception
        handler can be exercised).
    raise_on_heartbeat:
        If ``True``, ``heartbeat()`` raises ``RuntimeError``.
    """

    def __init__(
        self,
        default_status: SendStatus = SendStatus.HANDLED,
        responses: dict[type[OngwatchEvent], SendStatus] | None = None,
        raise_on_send: bool = False,
        raise_on_heartbeat: bool = False,
    ) -> None:
        self.default_status = default_status
        self.responses: dict[type[OngwatchEvent], SendStatus] = responses or {}
        self.raise_on_send = raise_on_send
        self.raise_on_heartbeat = raise_on_heartbeat

        self.received: list[OngwatchEvent] = []
        self.heartbeat_count: int = 0
        self.started: bool = False
        self.stopped: bool = False

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    async def send(self, event: OngwatchEvent) -> SendStatus:
        if self.raise_on_send:
            raise RuntimeError("MockOutput.send() deliberately raised")
        self.received.append(event)
        return self.responses.get(type(event), self.default_status)

    async def heartbeat(self) -> None:
        if self.raise_on_heartbeat:
            raise RuntimeError("MockOutput.heartbeat() deliberately raised")
        self.heartbeat_count += 1
