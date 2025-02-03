# FIXME: switch to use astro, maybe?
import argparse
# import logging
import logging
from typing import Dict

import socketio
from tdvutil import ppretty

from _ongwatch.util import log, now, out, printsupport


class OngWatch_SE(socketio.AsyncClientNamespace):
    botargs: argparse.Namespace
    token: str

    def __init__(self, args: argparse.Namespace, logger: logging.Logger, token: str, namespace: str = '/') -> None:
        self.botargs = args
        self.token = token
        self.logger = logger

        super().__init__(namespace)

    async def on_connect(self):
        self.logger.info('connection established')
        # sio.emit('authenticate', {"method": "jwt", "token": JWT})
        # creds = get_credentials(Path('credentials.toml'), 'test')
        await self.emit('authenticate', {"method": "apikey", "token": self.token})

    async def on_disconnect(self, reason="<no reason>"):
        self.logger.warning(f'disconnect reason: {reason}')

    async def on_authenticated(self, data):
        self.logger.info(f"Authenticated: {data}")
        # self.logger.info(f"Namespace: {self.namespace}")
        # await self.emit('subscribe', {"topic": "channel.follow"})

    async def on_connect_error(self, data):
        self.logger.error("The connection failed!")

    async def on_unauthorized(self, data):
        self.logger.error(f"Unauthorized: {data}")

    async def on_event(self, event, extra):
        t = event['type']

        if t == "tip":
            if event.get("isMock", False):
                type = "Tip_TEST"
            else:
                type = "Tip"
            amount = event['data']['amount']
            user = event['data']['displayName']

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

async def start(args: argparse.Namespace, creds: Dict[str, str]|None, logger: logging.Logger):
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
    sio.register_namespace(OngWatch_SE(args, logger, token, "/"))

    logger.info(f"Starting Streamelements backend")
    await sio.connect(connect_url, transports=["websocket"], headers={"Content-Type": "application/json"})
    await sio.wait()
