# FIXME: switch to use astro, maybe?
import argparse
# import logging
import logging
from typing import Dict

import socketio
from tdvutil import ppretty

from _ongwatch.util import log, now, out, printsupport

# INFO:engineio.client:Received packet MESSAGE data 2["event:update",{"name":"tip-latest","data":{"amount":10,"avatar":"https://cdn.streamelements.com/assets/dashboard/my-overlays/overlay-default-preview-2.jpg","displayName":"Clare","providerId":"156801396","name":"clare"},"provider":"twitch","channel":"594a9f426e9dd856f439d15a","activityId":"6793bcc4dea98647a8967fe5","isMock":true},{"ts":1737735364714,"nonce":"e41b73d0-9ae8-4f15-9422-59bfb5358c3b"}]
# INFO: socketio.client: Received event "event:update" [/ ]
# INFO: engineio.client: Received packet MESSAGE data 2["event", {"channel": "594a9f426e9dd856f439d15a", "provider": "twitch", "type": "tip", "createdAt": "2025-01-24T16:16:02.771Z", "isMock": true, "data": {"amount": 10, "avatar": "https://cdn.streamelements.com/assets/dashboard/my-overlays/overlay-default-preview-2.jpg", "displayName": "Clare", "username": "clare", "providerId": "156801396"}, "updatedAt": "2025-01-24T16:16:04.714Z", "_id": "6793bcc4dea98647a8967fe5", "activityId": "6793bcc4dea98647a8967fe5", "sessionEventsCount": 1}, {"ts": 1737735364714, "nonce": "d4a3589f-2f85-468e-b653-327f058f7263"}]
# INFO: socketio.client: Received event "event" [/ ]


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

    # @sio.event
    # def my_message(data):
    #     log('message received with ', data)
    #     sio.emit('my response', {'response': 'my response'})


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
            if event['isMock']:
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
