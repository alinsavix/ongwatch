# FIXME: switch to use astro, maybe?
import argparse
# import logging
import logging
from typing import Any, Dict

import socketio
from tdvutil import ppretty

from _ongwatch.util import get_json_url, log, now, out, printsupport


# FIXME: many of the handlers need their arguments to be properly typed
class OngWatch_SL(socketio.AsyncClientNamespace):
    botargs: argparse.Namespace
    info: Dict[str, Any]|None
    logger: logging.Logger

    def __init__(self, args: argparse.Namespace, logger: logging.Logger, info: Dict[str, Any] | None, namespace: str = '/') -> None:
        self.botargs = args
        self.info = info
        self.logger = logger

        super().__init__(namespace)

    async def on_connect(self) -> None:
        self.logger.info('connection established')

    async def on_disconnect(self, reason: str = "<no reason>") -> None:
        self.logger.warning(f'disconnect reason: {reason}')

    # async def on_authenticated(self, data):
    #     self.logger.warning(f"Authenticated: {data}")
    #     self.logger.warning(f"Namespace: {self.namespace}")
    #     # await self.emit('subscribe', {"topic": "channel.follow"})

    async def on_connect_error(self, data: Any) -> None:
        self.logger.error(f"SL: The connection failed: {data}")

    async def on_unauthorized(self, data: Any) -> None:
        self.logger.error(f"SL: Unauthorized: {data}")

    async def on_event(self, event: Any, extra: Any = None) -> None:
        t = event["type"]

        if t == "donation":
            amount = float(event["message"][0].get("amount", 0.0))
            user = event["message"][0].get("from", "UnknownUser")
            if event["message"][0].get("isTest", False):
                type = "Tip_TEST"
            else:
                type = "Tip"

            printsupport(now(), supporter=user, type=type, amount=amount)
            self.logger.info(f"output tip: {amount} by {user}")
        else:
            self.logger.debug(f"Ignoring event of type {t}: {event}")

# @sio.on('*')
# def any_event(data):
#     print(f"Received wildcard event: {event}, sid: {sid}, data: {data}")

# @sio.event
# def message(data):
#     log(f"Received message: {data}")

# FIXME: support socket tokens, not this ghetto undocumented thing
async def start(args: argparse.Namespace, creds: Dict[str, str]|None, logger: logging.Logger) -> None:
    if creds is None:
        raise ValueError("No credentials specified")

    token = creds['socket_token']
    connect_url = f"https://sockets.streamlabs.com?token={token}"
    info = None

    eiologger = logging.getLogger("streamlabs.client")
    eiologger.setLevel(logging.WARNING)

    sio = socketio.AsyncClient(logger=logger, engineio_logger=eiologger, reconnection=True)
    sio.register_namespace(OngWatch_SL(args, logger, info, "/"))

    logger.info(f"Starting Streamlabs backend")
    await sio.connect(connect_url, transports=['websocket'], headers={"Content-Type": "application/json"})
    await sio.wait()
