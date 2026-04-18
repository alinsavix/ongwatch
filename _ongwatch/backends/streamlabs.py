from __future__ import annotations

# FIXME: switch to use astro, maybe?
import argparse
import logging
from datetime import datetime, timezone
from typing import Any, Dict

import socketio

from ..dispatcher import Dispatcher
from ..events import CashSupportEvent

# ---------------------------------------------------------------------------
# Pure mapping functions
# ---------------------------------------------------------------------------

def _map_donation_event(event: Dict[str, Any]) -> CashSupportEvent:
    msg = event["message"][0]
    amount = float(msg.get("amount", 0.0))
    user = msg.get("from", "UnknownUser")
    is_test = msg.get("isTest", False)
    return CashSupportEvent(
        timestamp=datetime.now(tz=timezone.utc),
        backend="streamlabs",
        raw=event,
        username=user,
        amount=amount,
        kind="tip_test" if is_test else "donation",
    )


# ---------------------------------------------------------------------------
# Streamlabs socket.io namespace
# ---------------------------------------------------------------------------

# FIXME: many of the handlers need their arguments to be properly typed
class OngWatch_SL(socketio.AsyncClientNamespace):
    botargs: argparse.Namespace
    info: Dict[str, Any] | None
    logger: logging.Logger
    dispatcher: Dispatcher

    def __init__(
        self,
        args: argparse.Namespace,
        logger: logging.Logger,
        info: Dict[str, Any] | None,
        dispatcher: Dispatcher,
        namespace: str = '/',
    ) -> None:
        self.botargs = args
        self.info = info
        self.logger = logger
        self.dispatcher = dispatcher

        super().__init__(namespace)

    async def on_connect(self) -> None:
        self.logger.info('connection established')

    async def on_disconnect(self, reason: str = "<no reason>") -> None:
        self.logger.warning(f'disconnect reason: {reason}')

    async def on_connect_error(self, data: Any) -> None:
        self.logger.error(f"SL: The connection failed: {data}")

    async def on_unauthorized(self, data: Any) -> None:
        self.logger.error(f"SL: Unauthorized: {data}")

    async def on_event(self, event: Any, extra: Any = None) -> None:
        t = event["type"]

        if t == "donation":
            evt = _map_donation_event(event)
            self.logger.info(f"Donation: {evt.amount} from {evt.username}")
            self.dispatcher.emit(evt)
        else:
            self.logger.debug(f"Ignoring event of type {t}: {event}")


# FIXME: support socket tokens, not this ghetto undocumented thing
async def start(
    args: argparse.Namespace,
    creds: Dict[str, str] | None,
    logger: logging.Logger,
    dispatcher: Dispatcher,
) -> None:
    if creds is None:
        raise ValueError("No credentials specified")

    token = creds['socket_token']
    connect_url = f"https://sockets.streamlabs.com?token={token}"
    info = None

    eiologger = logging.getLogger("streamlabs.client")
    eiologger.setLevel(logging.WARNING)

    sio = socketio.AsyncClient(logger=logger, engineio_logger=eiologger, reconnection=True)
    sio.register_namespace(OngWatch_SL(args, logger, info, dispatcher, "/"))

    try:
        logger.info("Starting Streamlabs backend")
        await sio.connect(connect_url, transports=['websocket'], headers={"Content-Type": "application/json"})
        await sio.wait()
    except Exception as e:
        logger.error(f"exception: {e}")
        raise
    finally:
        await sio.disconnect()
