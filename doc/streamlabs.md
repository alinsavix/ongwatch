# Streamlabs

## Example Events

A tip event looks like:

```json
{
    "type": "donation",
    "message": [
        {
            "name": "alinsa_vix",
            "message": "This is a test donation for $97.00",
            "from": "Kevin",
            "to": {
                "name": "alinsa_vix"
            },
            "from_user_id": 1,
            "amount": 97,
            "formattedAmount": "$97.00",
            "currency": "USD",
            "recurring": false,
            "isTest": true,
            "isPreview": false,
            "unsavedSettings": [],
            "_id": "ef30fdbe7c9860425952ecd72c9ea65f",
            "priority": 10
        }
    ],
    "for": "streamlabs",
    "event_id": "evt_7e840c8183f7253b4cc8ffaa8ce6e2a9"
}
```

## Auth Tokens

### Option #1 - API key from an overlay URL

You can treat the last part of a Streamlabs overlay as an api key, to let you
retrieve a struct that says how to connect via SocketIO. This isn't nearly as
straightforward as it is with StreamElements, and it's not even suggested 
by anyone to be a good idea -- plus, Alinsa reverse engineered it (if you can
call it that) from live Streamlabs overlays, so it could change or vaporize
at any point. Still, documenting here in case it is useful.

Streamlabs overlay URLs are in the form of:

```
    https://streamlabs.com/alert-box/v3/{apikey}
```

With that API key, you can connect by doing something like:


```python
apikey = "<whatever>"
token_url = f"https://streamlabs.com/api/v5/io/info?token={apikey}"
info = await get_json_url(token_url)
sio = socketio.AsyncClient(
    logger=True, engineio_logger=True, reconnection=True,
    reconnection_attempts=info["settings"]["reconnect_attempts"],
    reconnection_delay=info["settings"]["reconnect_delay"] / 1000,
    reconnection_delay_max=info["settings"]["reconnect_delay_max"] / 1000
)
connect_url = info["path"]
await sio.connect(connect_url, transports=['websocket'], headers={"Content-Type": "application/json"})
```

The struct returned by the "info" endpoint looks like:

```json
{
    'path': 'https://aws-io.streamlabs...z2IeiTBCzE7dNRlHUkOwnMZM',
    'settings': {
            'reconnect_delay_max': 60000,
            'reconnect_attempts': 10,
            'timeout': 5000,
            'transports': ['websocket', 'polling'],
            'reconnect_delay': 38000
    },
    'platforms': {'twitch_account': '129765209'},
    'platforms2': {'twitch_account': '129765209'},
    'thirdpartyplatforms': []
}
```

This method is not currently supported by the ongwatch code, but it would be trivial
for someone to add.


### Option #2 - Socket API Token

Streamlabs has a "socket API" token that can be used to listen to events. The streamer
can retrieve this token on the Streamlabs site by going to
[https://streamlabs.com/dashboard#/settings/api-settings](the API settings page),
under the "API Tokens" sub-tab, and then clicking "copy" next to the "Your Socket
API Token" field.

This token should be placed in the Streamlabs section of `credentials.toml` under
a "socket_token" key.

This token does not expire.


## Other notes

We can route connections through a proxy via something like:

```python
session = requests.Session()
session.proxies = {
    "http": "http://127.0.0.1:8888",
    "https": "http://127.0.0.1:8888",
}

sio = socketio.Client(http_session=session, logger=True, engineio_logger=True)
sio = socketio.AsyncClient(logger=True, engineio_logger=True)
```

And do some http(s) debugging with:

```python
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
```
