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

def _map_tip_event(event: Dict[str, Any]) -> CashSupportEvent:
    amount = float(event['data'].get("amount", 0.0))
    user = event['data'].get("username", "UnknownUser")
    is_mock = event.get("isMock", False)
    return CashSupportEvent(
        timestamp=datetime.now(tz=timezone.utc),
        backend="streamelements",
        raw=event,
        username=user,
        amount=amount,
        kind="tip_test" if is_mock else "tip",
    )


# ---------------------------------------------------------------------------
# StreamElements socket.io namespace
# ---------------------------------------------------------------------------

# FIXME: many of the handlers need their arguments to be properly typed
class OngWatch_SE(socketio.AsyncClientNamespace):
    botargs: argparse.Namespace
    token: str
    logger: logging.Logger
    dispatcher: Dispatcher

    def __init__(
        self,
        args: argparse.Namespace,
        logger: logging.Logger,
        token: str,
        dispatcher: Dispatcher,
        namespace: str = '/',
    ) -> None:
        self.botargs = args
        self.token = token
        self.logger = logger
        self.dispatcher = dispatcher

        super().__init__(namespace)

    async def on_connect(self) -> None:
        self.logger.info('connection established')
        await self.emit('authenticate', {"method": "apikey", "token": self.token})

    async def on_disconnect(self, reason: str = "<no reason>") -> None:
        self.logger.warning(f'disconnect reason: {reason}')

    async def on_authenticated(self, data: Any) -> None:
        self.logger.info(f"Authenticated: {data}")

    async def on_connect_error(self, data: Any) -> None:
        self.logger.error("The connection failed!")

    async def on_unauthorized(self, data: Any) -> None:
        self.logger.error(f"Unauthorized: {data}")

    async def on_event(self, event: Any, extra: Any) -> None:
        t = event['type']
        if t == "tip":
            evt = _map_tip_event(event)
            self.logger.info(f"Tip: {evt.amount} from {evt.username}")
            self.dispatcher.emit(evt)
        else:
            self.logger.debug(f"Ignoring event of type {t}: {event}")


async def start(
    args: argparse.Namespace,
    creds: Dict[str, str] | None,
    logger: logging.Logger,
    dispatcher: Dispatcher,
) -> None:
    if creds is None:
        raise ValueError("No credentials specified")
    elif "apikey" in creds:
        token = creds["apikey"]
    elif "jwt" in creds:
        token = creds["jwt"]
    else:
        raise ValueError("No API key or JWT found in credentials")

    connect_url = "https://realtime.streamelements.com"
    eiologger = logging.getLogger("streamelements.client")
    eiologger.setLevel(logging.WARNING)

    sio = socketio.AsyncClient(logger=logger, engineio_logger=eiologger, reconnection=True)
    sio.register_namespace(OngWatch_SE(args, logger, token, dispatcher, "/"))

    try:
        logger.info("Starting Streamelements backend")
        await sio.connect(connect_url, transports=["websocket"], headers={"Content-Type": "application/json"})
        await sio.wait()
    except Exception as e:
        logger.error(f"exception: {e}")
        raise
    finally:
        await sio.disconnect()
