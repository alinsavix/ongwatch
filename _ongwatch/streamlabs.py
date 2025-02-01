# FIXME: switch to use astro, maybe?
import argparse
# import logging
from typing import Any, Dict

import socketio
from tdvutil import ppretty

from _ongwatch.util import get_json_url, log, now, out, printsupport

# The 'info' struct looks like:
# {
#     'path': 'https://aws-io.streamlabs...z2IeiTBCzE7dNRlHUkOwnMZM',
#     'settings': {
#             'reconnect_delay_max': 60000,
#             'reconnect_attempts': 10,
#             'timeout': 5000,
#             'transports': ['websocket', 'polling'],
#             'reconnect_delay': 38000
#     },
#     'platforms': {'twitch_account': '129765209'},
#     'platforms2': {'twitch_account': '129765209'},
#     'thirdpartyplatforms': []
# }

class SLWebSocketClosure(Exception):
    """Exception indicating closure of the WebSocket."""


# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

# session = requests.Session()
# session.proxies = {
#     "http": "http://127.0.0.1:8888",
#     "https": "http://127.0.0.1:8888",
# }

# sio = socketio.Client(http_session=session, logger=True, engineio_logger=True)
# sio = socketio.AsyncClient(logger=True, engineio_logger=True)


class OngWatch_SL(socketio.AsyncClientNamespace):
    botargs: argparse.Namespace
    info: Dict[str, Any]|None


    def __init__(self, args: argparse.Namespace, info: Dict[str, Any]|None, namespace: str = '/') -> None:
        self.botargs = args
        self.info = info

        super().__init__(namespace)

    async def on_connect(self):
        log('SL: connection established')
        # sio.emit('authenticate', {"method": "jwt", "token": JWT})
        # creds = get_credentials(Path('credentials.toml'), 'test')
        # await self.emit('authenticate', {"method": "apikey", "token": self.token})

    # @sio.event
    # def my_message(data):
    #     log('message received with ', data)
    #     sio.emit('my response', {'response': 'my response'})


    async def on_disconnect(self, reason="<no reason>"):
        log(f'SL: disconnect reason: {reason}')


    # async def on_authenticated(self, data):
    #     log(f"SL: Authenticated: {data}")
    #     log(f"SL: Namespace: {self.namespace}")
    #     # await self.emit('subscribe', {"topic": "channel.follow"})

    async def on_connect_error(self, data):
        log(f"SL: The connection failed: {data}")

    async def on_unauthorized(self, data):
        log(f"SL: Unauthorized: {data}")


    # tips look like:
    # {
    #    "type": "donation",
    #    "message": [
    #        {
    #            "name": "alinsa_vix",
    #            "message": "This is a test donation for $97.00",
    #            "from": "Kevin",
    #            "to": {
    #                "name": "alinsa_vix"
    #            },
    #            "from_user_id": 1,
    #            "amount": 97,
    #            "formattedAmount": "$97.00",
    #            "currency": "USD",
    #            "recurring": false,
    #            "isTest": true,
    #            "isPreview": false,
    #            "unsavedSettings": [],
    #            "_id": "ef30fdbe7c9860425952ecd72c9ea65f",
    #            "priority": 10
    #        }
    #      ],
    #      "for": "streamlabs",
    #      "event_id": "evt_7e840c8183f7253b4cc8ffaa8ce6e2a9"
    #  }
    async def on_event(self, event, extra=None):
        # log(f'XXX message received with"')
        # log(f"arg1 (self): {ppretty(self)}")
        # log(f"arg2 (zot): {ppretty(data)}")
        # log(f"arg3 (data): {ppretty(extra)}")
        t = event["type"]


        if t == "donation":
            amount = event["message"][0]["amount"]
            user = event["message"][0]["from"]
            if event["message"][0]["isTest"]:
                type = "Tip_TEST"
            else:
                type = "Tip"
            # log(f'XXX {t} {amount} {user}')
            printsupport(now(), supporter=user, type=type, amount=amount)
        else:
            log(f"SL: Ignoring event of type {t}: {event}")
        # sio.emit('my response', {'response': 'my response'})




# @sio.event
# def tip(data):
#     log(f"TIP: {data}")

# @sio.on('*')
# def catchall(msg):
#     log(f"catchall: {msg}")

# @sio.on('*')
# def any_event(data):
#     print(f"Received wildcard event: {event}, sid: {sid}, data: {data}")

# @sio.event
# def message(data):
#     log(f"Received message: {data}")

# FIXME: support socket tokens, not this ghetto undocumented thing
async def start(args: argparse.Namespace, creds: Dict[str, str]):
    # Commented out bits are for getting a connection using the last bit of the
    # overlay URL, which is a reverse engineered/undocumented thing. We should
    # make this selectable at some point.
    # if "apikey" in creds:
    #     token = creds["apikey"]
    # else:
    #     raise ValueError("No token found in credentials")
    #
    # token_url = f"https://streamlabs.com/api/v5/io/info?token={apikey}"
    # info = await get_json_url(token_url)
    # sio = socketio.AsyncClient(logger=True, engineio_logger=True, reconnection=True,
    #                            reconnection_attempts=info["settings"]["reconnect_attempts"],
    #                            reconnection_delay=info["settings"]["reconnect_delay"] / 1000,
    #                            reconnection_delay_max=info["settings"]["reconnect_delay_max"] / 1000
    #                        )
    # connect_url = info["path"]

    token = creds['socket_token']
    connect_url = f"https://sockets.streamlabs.com?token={token}"
    info = None
    sio = socketio.AsyncClient(logger=False, engineio_logger=False, reconnection=True)
    sio.register_namespace(OngWatch_SL(args, info, "/"))

    log(f"Starting Streamlabs backend")
    await sio.connect(connect_url, transports=['websocket'], headers={"Content-Type": "application/json"})
    await sio.wait()
