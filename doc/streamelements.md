# Streamelements

## Example events

A tip event from StreamElements looks like:
```json
{
    "channel": "594a9f426e9dd856f439d15a",
    "provider": "twitch",
    "type": "tip",
    "createdAt": "2025-01-24T16:16:02.771Z",
    "isMock": true,
    "data": {
        "amount": 10,
        "avatar": "https://cdn.streamelements.com/assets/dashboard/my-overlays/overlay-default-preview-2.jpg",
        "displayName": "Clare", 
        "username": "clare", 
        "providerId": "156801396"
    }, 
    "updatedAt": "2025-01-24T16:16:04.714Z", 
    "_id": "6793bcc4dea98647a8967fe5", 
    "activityId": "6793bcc4dea98647a8967fe5", 
    "sessionEventsCount": 1
}
```


## Auth tokens

### Option #1 - JWT token

Use a JWT token from the streamer's account, following the instructions
[here](https://dev.streamelements.com/docs/api-docs/ae133ffaf8c1a-personal-access-using-jwt-secert-token-to-access-the-api#obtaining-your-token).
Place the token under a key named `jwt` in the StreamElements section of `credentials.toml`

The JWT token expires after an undocumented amount of time, currently in the general range of
"several months".

### Option #2 - API key from an overlay URL

The URL for an overlay belonging to the streamer's account contains a key that can be used
directly to authenticate. The overlay URL will look something like:

```text
    https://streamelements.com/overlay/{overlay_id}/{apikey}
```

...where the {apikey} field is what you want to use. For example, in this URL:

```text
    https://streamelements.com/overlay/2ecb5fffe73e46b2fd32979/LpfJp3Szhi9tWevZeCML
```

...the API key would be `LpfJp3Szhi9tWevZeCML`.

Place the API key under a key named `apikey` in the StreamElements section of `credentials.toml`.

This not an officially supported way to authenticate, but several people involved with
StreamElements have unofficially indicated that there are no plans to change the current
behavior. This key does not expire.

### Option #3 - OAuth

Theoretically you can set up an OAuth app and use that to authenticate, and in theory that
authentication won't expire, but one must first be approved and set up by StreamElements,
and they seem extremely reluctant to do that, so this doesn't seem like an option,
currently.
