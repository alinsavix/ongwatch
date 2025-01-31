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



class SEWebSocketClosure(Exception):
    """Exception indicating closure of the WebSocket."""

# class ReconnectWebSocket(Exception):
#     """Exception indicating the need to reconnect to the websocket."""

#     def __init__(self, url: str) -> None:
#         self.url: str = url


# const options = {
#     method: 'GET',
#     headers: {'Content-Type': 'application/json', Authorization: 'Bearer JWT_TOKEN'}
# }

# fetch('https://api.streamelements.com/kappa/v2/activities/channel', options)
# .then(response=> response.json())
# .then(response=> console.log(response))
# .catch(err= > console.error(err))





# const socket = io('https://realtime.streamelements.com', {

#     transports: ['websocket']

# })

# def log(msg):
#     from datetime import datetime
#     current_time = datetime.now()
#     print(f"{current_time} {msg}")
#     sys.stdout.flush()


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
    info: Dict[str, Any]

    def __init__(self, args: argparse.Namespace, info: Dict[str, Any], namespace: str = '/') -> None:
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
        t = event['type']

        if t == "donation":
            amount = event['message'][0]['amount']
            user = event['message'][0]['from']
            # log(f'XXX {t} {amount} {user}')
            printsupport(now(), supporter=user, type="Tip", amount=amount)
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
    if "token" in creds:
        token = creds["token"]
    else:
        raise ValueError("No token found in credentials")

    token_url = f"https://streamlabs.com/api/v5/io/info?token={token}"
    info = await get_json_url(token_url)

    log(f"Starting Streamlabs backend")

    sio = socketio.AsyncClient(logger=True, engineio_logger=True, reconnection=True,
                               reconnection_attempts=info["settings"]["reconnect_attempts"],
                               reconnection_delay=info["settings"]["reconnect_delay"] / 1000,
                               reconnection_delay_max=info["settings"]["reconnect_delay_max"] / 1000)
    sio.register_namespace(OngWatch_SL(args, info, "/"))
    await sio.connect(info["path"], transports=['websocket'], headers={"Content-Type": "application/json"})
    await sio.wait()
