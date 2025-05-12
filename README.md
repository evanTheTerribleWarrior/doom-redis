DOOM Redis Edition
==================

Play Doom with a live Web UI showing real-time game stats, leaderboards, chat and in-game notifications for specific events like killing spree --- powered by Redis and WebSockets.


Player Search and achievements
![Image](https://github.com/user-attachments/assets/b1296b31-23da-4133-8671-cf9bc685b2ff)

Real time dashboards
![Image3](https://github.com/user-attachments/assets/d84a7394-d423-455c-9c83-ddd04bb44ba3)

Custom rewards and boosts
![Image2](https://github.com/user-attachments/assets/329c4bd6-f414-4d7e-98c3-41e0339f1527)

Custom in-game notifications
![Image4](https://github.com/user-attachments/assets/46b5c25e-7c9a-4b7e-b0ab-e6fd31906a24)

Efficiency tracking
![Image5](https://github.com/user-attachments/assets/31790c3f-e83a-49e5-bbf5-404c2276cb47)

Current Features
--------

-   Live player chat feed (Redis Streams), enabled by pressing "c"

-   Live game event log feed (Redis Streams)

-   Real-time leaderboards and per-map domination tracking (Redis Streams)

-   Real-time in-game notifications (Redis PubSub)

-   Player Search (Redis Autocomplete - FT.SUGGET)

-   Player Performance over time (Redis Timeseries)

-   Weapon Recommendation (Redis Vector Search)

-   Achievement badges (Redis BitMap)

-   Reward System. Get extra ammo, guns or go to GODMODE for a 50 kill streak!

-   Data separation per Doom WAD and per Map

-   Using Redis pipeline to execute operations more efficiently

Work in Progress
--------

-   More cases of in-game notifications
-   Looking for other cool ideas!
-   Test/build on windows and Linux

Fixes
--------

TBC

Project Structure
-----------------

```
/
├── backend/           # Python Flask + Socket.IO server (real-time event broadcasting)
├── build/             # Scripts to automate deployment of backend, frontend and game
├── frontend/          # React-based frontend UI (game logs, player chat, leaderboards)
├── game-code/         # DOOM source code (modified for Redis integration)
├── README.md          # This file
└── .env.example       # Environment variables (Redis host, port, etc.)

```

Quick Start
-----------

Requirements:

-   Python 3.11+

-   Node.js + npm

-   Redis server (local or cloud)

-   Linux/macOS system

-   cmake/gcc

###  **Clone the repository**

```
git clone https://github.com/your-username/doom-redis.git
cd doom-redis

```

###  **Add a WAD file**

The repo comes with a downloaded version of Freedoom 1 & 2. 
You can find them under the `game-code/WADs` folder.

You can include your own WADs under that folder and read from them at runtime

###  **Edit environment variables**

```
cp .env.example .env
```

Modify `.env` accordingly:

```
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
SOUNDFONT=gzdoom.sf2
PLAYER_PASSWORD=default
PLAYER_NAME=
WAD_NAME=
ENABLE_VECTOR=1

```

If you are using an external Redis instance please set the `REDIS_` values accordingly

Please set `PLAYER_NAME` and `WAD_NAME` based on the player name you want and the wad name you have in the WADs directory that you want to use

The `.env.example` file comes with a default `PLAYER_PASSWORD`. Add your own. This is an extremely simple way to avoid clashes e.g. when one player might set the same `playerName` as an existing one and mess up the stats. So you will need your own unique `playerName` which keeps things cleaner.

Obviously this is a free repo with intention to have fun with a common Redis server, so it does not come with security-first principles!

`SOUNDFONT`: This will allow you to load a soundfont file to be used for music in the game. If you don't want sound leave this empty

`ENABLE_VECTOR`: Whether it should enable notifications related to Vector Searches. For example,
a player might be notified if another player had a killing spree using a specific weapon at a point in the map

The script will load these variables both for the game code and the backend to read

###  **Run the project via single script**

From the root directory run the script for your OS, for example for macOS:

```
cd build
bash start-macos.sh

```

This will:

-   Build the Doom game

-   Set up backend (Python server)

-   Set up frontend (React UI)

-   Launch everything in proper order

Build manually (no script)
-----------

If you wish to run everything individually you should:

###  **Compile the Doom game**
```
cd game-code
mkdir build
cmake ..
make
```
This will generate the `redis-doom` binary inside `game-code/build`

Note: If you want to re-build everything, you need to delete all the files/folders under
the `game-code/build` directory and then run again cmake + make as per above

###  **Setup the backend**
```
cd backend

# Create a virtual environment (only once)
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the backend server
python3 app.py
```
Note: The backend expects a Redis server to be running based on your .env settings

###  **Setup frontend**
```
cd frontend

# Install node modules (only once)
npm install

# Start the React development server
npm start
```

###  **Populate env variables via export**

The current `.env` file is like this:

```
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
SOUNDFONT=gzdoom.sf2
PLAYER_PASSWORD=default
PLAYER_NAME=
WAD_NAME=
```

You need to export at least the `PLAYER_PASSWORD`:
```
export PLAYER_PASSWORD=TestPassword
```

You can also export `PLAYER_NAME` or set it as parameter in the command line as shown below

###  **Run the game**
```
cd game-code/build

# Replace DOOM.WAD with your WAD filename if different, and optionally add -playerName
# if not already set in .env
./redis-doom -iwad ../WADs/freedoom1.wad -playerName DoomSlayer
```

Project Architecture
--------------------

If you want to look into the implementation details, check for the files:
```
game-code/include/redis-doom.h
game-code/src/redis-doom.c
```
+-----------------------------------------------------------+

|                          Doom Game (C)                    |

|                  (hiredis → Redis Streams)                 |

+-----------------------------------------------------------+

                         ↓

+-----------------------------------------------------------+

|                Redis Server (localhost:6379)              |

|            doom:events            doom:chat               |

+-----------------------------------------------------------+

                         ↓

+-----------------------------------------------------------+

|                   Flask Backend + Socket.IO               |

|                (Eventlet async WebSocket server)          |

+-----------------------------------------------------------+

                         ↓

+-----------------------------------------------------------+

|             React + Material UI Frontend (port 3000)      |

|        Live Chat | Game Logs | Player Leaderboard         |

+-----------------------------------------------------------+

Implementation Details
--------------------

Below are some examples of how currently some features are implemented (May 2025).

### Live Chat

In the Doom C code, several additions have been made in the main built-in functions used for generating text lines on the screen. Here is an example from `hu_stuff.c`
```
// If we are in Redis chat mode, we clear the line
    // and then add > as the start of the chat line
    // Finally we receive the input as player types
    if (redischatmode) {
        HUlib_clearTextLine(&w_redischatinput);
        HUlib_addCharToTextLine(&w_redischatinput, '>');
        HUlib_addCharToTextLine(&w_redischatinput, ' ');
        for (int i = 0; i < redischatlen; ++i)
            HUlib_addCharToTextLine(&w_redischatinput, redischatbuffer[i]);
    }
```

The "chat mode" gets enabled when pressing "c" on the keyboard. 
At that point a text line is initiated that starts with ">" and then we
read the characters the users presses into a buffer and then into the text line

Chat messages are sent as events in the backend, as per `redis_doom.c`:
```
void AddChatEvent(redisContext *c, const char *playerName, const char *message)
{
    redisReply *reply;

    reply = redisCommand(c, "XADD doom:chat * playerName %s message %s", playerName, message);
    FreeRedisReply(reply);
}
```

Then these messages are picked up by the backend (`backend/consumer.py`)
```
def start_chat_consumer(r, socketio):
```

and are send via websocket to the frontend

### WAD ID generation

This is an important part in order to be able to create per-WAD separation of the various data.

So this takes advantage of an existing Doom function `W_Checksum` that basically creates a hash of all the data/lumps of a WAD.

So the following function outputs a hex representation of that to generate ultimately a unique string per WAD, so we don't rely on filenames as those can be easily changed from a user
```
void CalculateWADHash(void) 
{
    sha1_digest_t digest;
    W_Checksum(digest);

    for (int i = 0; i < 20; ++i) {
        sprintf(doom_wad_id + i * 2, "%02x", digest[i]);
    }
    doom_wad_id[40] = '\0';

    printf("[WAD Hash] WAD ID: %s\n", doom_wad_id);
}
```

Then this is sent via all events as needed to the backend, for example:
```
reply = redisCommand(c, "XADD doom:events * type kill playerName %s targetName %s weaponName %s mapName %s wadId %s", playerName, targetName, weaponName, mapName, doom_wad_id);
```

A hash is maintained as `doom:wads:wad-names` that is a basic way of maintaining a pair of
wadID - filename. 
```
void SendWADHashToRedis(redisContext *c, const char *iwad_filename) 
{
    redisReply* reply;

    reply = redisCommand(c, "HSETNX doom:wads:wad-names %s %s", doom_wad_id, iwad_filename);
    FreeRedisReply(reply);
}
```

It's not bulletproof but good enough for this sample repo in order to render the right filename in the frontend

### Vector Search

The repo has logic to create baseline for vector searches for multiple use cases.

As of writing these lines, the use cases used as testing ground is about notifying the current player if in a location nearby we can recommend a good weapon based on killing sprees of previous players.

The sequence is as follows:
- Create vector search index only once in `consumer.py` to be used for future searches
- When a player performs a spree, we add the spree as a hash with a vector mapping
```
if kill_spree is not None:
    posX = safe_decode(data.get(b'posX', b''))
    posY = safe_decode(data.get(b'posY', b''))
    vector_mapping = get_vector_mapping(player, weapon, mapname, wadId, float(posX), float(posY))
    spree_id = str(uuid.uuid4())
    key = f'doom:ai:vectors:sprees:{spree_id}'
    pipe.hset(key, mapping = vector_mapping)
    pipe.publish(BROADCAST_CHANNEL, kill_spree)
```

We include the current position of the player that we got from the C code (`AddKillToStream` function)

- Then as the player moves through the level we perform KNN vector search every X seconds to see if 
we get a hit in terms of other player sprees

- If we find, we send notification about the recommended  weapon 
```
if match.player != player:
    if(match.wadId == wadId and match.mapname == mapname):
        r.publish(f"doom:player:{player}", f"Recommended Weapon here: {match.weapon}")
        r.set(notification_key, value="1",ex=NOTIFICATION_EXPIRY)
```
We set NOTIFICATION_EXPIRY for the seconds that we want to wait until we expire the notification so that we don't overwhelm the player with notifications for every bit that they move


More implementation details will be added

Tests
-------

Currently tested on MacOS environment only

License
-------

-   The original Doom source code is under **GPL v2**.

-   This project adds new code under the **MIT License**.

-   Game assets use [Freedoom](https://freedoom.github.io/) (BSD-like license).

Credits
-------

-   Doom source: id Software

-   Freedoom assets: Freedoom Project

-   Hiredis: Redis

-   SDL2-Doom repo (https://github.com/AlexOberhofer/sdl2-doom)

Note
-------

This repo is just for fun and to play around with friends. 
It does not take into account things like session management and other mechanisms
that might matter in online games that share stats.

Anyway, happy playing and feel free to suggest additions that will make it more fun!