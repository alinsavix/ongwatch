# Ongwatch - Watch for stream events, and share them

## The Problem

Alinsa serves as the main tech bitch for the stream of the musician [Jonathan Ong](https://twitch.tv/JonathanOng) -- a stream that is both moderately complex (multiple bots, lots of hardware) and relatively long in the tooth (this year is the stream's 8th anniversary) -- which means it's picked up a decent number of different bots & codebases for making various parts of the stream work. As part of keeping the stream going, she's noticed several recurring pain points that have limited us in various ways:

First, each bot needs to individually manage the interface of each individual backend it cares about (Twitch, StreamElements, Streamlabs, etc), along with the authentication needed for each -- and these interfaces aren't always straightforward, and things like refreshing expiring authentications become pretty inconvenient issues (plus the more different systems and different programmers there are, the greater the chance of at least one of them getting things just... wrong)

Second, it's difficult for multiple bots to work together. This isn't a problem if a streamer wants to have a single bot that handles absolutely everything on a stream, but that's not always practical -- sometimes a bot doesn't have all the features one needs, sometimes there's different developers with their own toolset, sometimes there's existing bots that aren't trivial to port into a new framework... whatever the reason, it's sometimes pretty useful to allow bots to work together.

As an example of the second point, on Dr. Ong's stream, we have multiple bots that handle different things on the stream:

* One that handles cheers and tips and triggers various alerts
* One that monitors the MIDI output of an RC-202 Loopstation to calculate the tempo (bpm) of the song currently being played
* One that manages the lighting, making changes based on various criteria (including, but not limited to, when certain alerts are fired)
* One that monitors the MIDI data from specific instruments for stats gathering ("how energetically is Jon playing?") and for visualization purposes
  
Recently, we had an idea to start having the lighting in the room be more reactive, having the lighting change (handled by the lighting bot) based on the tempo of the song (which requires the bpm bot), how much support there has been (which requires the cheer/tip bot), and how energetically Jon is playing (which requires the MIDI bot). With the current setup, there is simply no way to have all these functions be handled by the same bot -- two of them, at a minimum, need to be running on very specific systems to be able to get a copy of the MIDI data they need.

It's possible to have those bots talk to each other directly, but as more bots are involved, the complexity ramps up quickly: With 4 bots (plus OBS, if we want to sync things based on current scene) there are *ten* separate pairs of hosts that might need to communicate! Each bot might have its own address, port, and protocol (websocket, socket.io, http, protobuf), and every bot that communicates with it must have some way to know these things (generally requiring a config file for each), so things quickly become pretty painful to manage.

## The Idea

The idea Alinsa has been rolling around in her head, and bouncing off of other people, is basically to have a "message bus" that bots (or non-bots) can use to share specific events as they happen, where every bot can listen for whatever types of events they specifically care about -- and publish data that they are authoritative for.

Streamers can add any kind of tool or bot they want as publishers (or listeners) onto this bus, but one publisher that most streamers will likely have is something that listens for events from the common streaming backends (e.g. Twitch, StreamElements, and Streamlabs), puts them into a useful format, and publishes them to the bus -- basically, have a way to publish major events happening on the stream so other tools can make use of them, without needing to individually authenticate and process things for themselves.

That 'core' functionality is also one of the major components of this repository: This repository is intended as a testbed for this idea and as an attempt to get things developed to the point it can be useful, and that core bot will be part of that (since why do any of this, if we have no events to feed into the system?)

## An Example

As an extremely simple example, let's take the case of someone cheering on Twitch. In very rough pseudocode, a normal bot that took an action might look like this (or some callback-based form of this):

```text
if !authenticated:
    start_local_webserver_for_oauth()
    call_oauth_library()
    wait_on_oauth_completion()
    write_tokens_to_file()

connect_to_provider()

while True:
    if token_expiry_is_soon():
        refresh_token()
        write_tokens_to_file()

    wait_on_event()
    if event == "cheer":
        print "We got a cheer of {tip.amount} from {tip.user}"
```

Some of this might be partially hidden by provider-specific libraries, but you get the idea. Note how little of this code is related to actually handling the events from the provider (3 lines out of 15, really)

In our new world, our central bot would process that same tip event, but would publish it into a MQTT topic, such as `stream/support/tips`. The message getting published might look like:

```json
{ "provider": "twitch", "user": "alinsa_vix", "amount": 2490, "message": "Cheer2490 CHAOS" }
```

And then the code to actually process the event might look like:

```text
connect_to_mqtt()
mqtt_subscribe("stream/support/cheers")

while True:
    wait_on_mqtt_message()
    if event.topic == "stream/support/cheers":
        print "We got a cheer of {cheer.amount} from {cheer.user}"
```

Still roughly 3 lines of code for actually handling an event, but now that's 3 lines out of 6!

If this bot then wanted to, say, make a judgement for how much hype there has been in the stream recently, and publish information for other bots or tools to use... well, there can't be example code on how to do that in the traditional world, because there's nowhere to publish that information **to**. At best, the bot could start an internal web server and allow other bots to query for the data, but that can start to add a lot of complexity.

In our new world, though, making that decision and publishing it might look something like:

```text
hype_level = leaky_bucket_contributions(cheer.amount)
mqtt_publish("stream/synthetic/hype", hype_level)
```

...and then any bots or tools that cared could subscribe to `stream/synthetic/hype` and work from there.

Or you could turn on a MQTT-controllable light if the hype reaches a certain level:

```text
if hype_level > 3:
    mqtt_publish("house/lights/light1/state", "ON")
else:
    mqtt_publish("house/lights/light1/state", "OFF")
```

## Current status (as of 2025-03-13)

Currently, we have a functional set of connections to the major backends -- Twitch, StreamElements, and Streamlabs -- Alinsa needed this for other reasons, and decided to use it as the starting point for this project. This seems to work well, and is done in a relatively pluggable way.

In progress is work to:

* Define the structure of the MQTT topic names that will be used to publish activity
* Define the data structures that will be published
* Define a sane API so that the bot can publish different places in different ways, from simple log files, to really heavyweight message queues

## Work in progress!

This is *definitely* a work in progress, and you shouldn't rely on it to function at all, at any point. Seriously.

If you have input into the idea (or actual code), feel free to reach out. Alinsa doesn't bite! Much. Thoughts from outside of her normal circle are eagerly accepted!

And yes, the "ongwatch" name is probably temporary, pending having any kind of good idea what else to call this.

## How to use

Setup is pretty rough right now. The short version

* Set up a python venv, activate it, and `pip install -r requirements.txt`
* Create a bot for yourself in the Twitch dev interface
* Create a `credentials.toml` with credentials for Twitch, StreamElements, and Streamlabs (see below)
* `./ongwatch.py --auth twitch` to get proper Twitch OAuth tokens
* `./ongwatch.py` to start everything up


## Setting up credentials.toml

You can optionally specify an "environment" (dev, prod, etc) for ongwatch to use, with `--environment <whatever>`. The default environment is `test`. Each of the entries in the credentials file is specific to an environment.

Example file, with notes inline:

```toml
# The OAuth client and secret as provided by twitch. We use the device code
# flow, so no OAuth callback URL (or local webserver) is needed. You can use
# the same client id across all your environments, if desired.
#
# If you want to use the local twitch mock websocket server (provided by the
# twitch CLI), use "localdev" as your environment name
[twitch.test]
client_id = 'abcdefg[...]xyz'
client_secret = 'zyxwvut[...]cba'

# For StreamElements, the JWT token you can get via their API expires, so
# it's not ideal to use for this. Instead, use the api key, which is the last
# segment of the URL to an overlay associated with the streamer's account.
# This key doesn't expire (otherwise peoples' overlays would periodically
# break), so just use that.
#
# There might be SOME functionality that is not available using this api key,
# but most of the critical stuff seems to work fine.
#
# Theoretically StreamElements OAuth tokens don't expire, but it seems to
# be nearly impossible to actually get StreamElements to give out OAuth
# access.
[streamelements.test]
apikey = "querty-tsS20-abcdxyz"

# From settings > API settings > API Tokens > Your Socket API Token
[streamlabs.test]
socket_token = "quertyOhMyThisIsAVeryLongTokenOrMaybeJustACryForHelp"
```
