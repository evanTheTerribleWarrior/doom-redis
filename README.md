DOOM Redis Edition
==================

Play Doom with a live Web UI showing real-time game stats, leaderboards, chat and in-game notifications for specific events like killing spree --- powered by Redis and WebSockets.

![Image](https://github.com/user-attachments/assets/a97bd1cf-cfb2-4185-b1fe-5703b738259c)

![Image2](https://github.com/user-attachments/assets/8c39c1fc-b4b9-4be4-b187-7f824ca6289e)

![Image3](https://github.com/user-attachments/assets/d84a7394-d423-455c-9c83-ddd04bb44ba3)

![Image4](https://github.com/user-attachments/assets/46b5c25e-7c9a-4b7e-b0ab-e6fd31906a24)

* * * * *

Current Features
--------

-   Live player chat feed (Redis Streams)

-   Live game event log feed (Redis Streams)

-   Real-time leaderboards and per-map domination tracking (Redis Streams)

-   Real-time in-game notifications (Redis PubSub)

-   Player Search (Redis Autocomplete - FT.SUGGET)

-   Data separation per Doom WAD and per Map

* * * * *

Work in Progress
--------

-   More cases of in-game notifications
-   Looking for other cool ideas!
-   Test/build on windows and Linux

* * * * *

Fixes
--------

- Currently working to fully fix the chat characters and what is actually printed

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

* * * * *

Quick Start
-----------

Requirements:

-   Python 3.11+

-   Node.js + npm

-   Redis server (local or cloud)

-   Linux/macOS system

-   cmake/gcc

1.  **Clone the repository**

```
git clone https://github.com/your-username/doom-redis.git
cd doom-redis

```

1.  **Add a WAD file**

The repo comes with a downloaded version of Freedoom 1 & 2. 
You can find them under the `game-code/WADs` folder.

You can include your own WADs under that folder and read from them at runtime

2.  **Edit environment variables**

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

```

If you are using an external Redis instance please set the `REDIS_` values accordingly

Please set `PLAYER_NAME` and `WAD_NAME` based on the player name you want and the wad name you have in the WADs directory that you want to use

The `.env.example` file comes with a default `PLAYER_PASSWORD`. Add your own. This is an extremely simple way to avoid clashes e.g. when one player might set the same `playerName` as an existing one and mess up the stats. So you will need your own unique `playerName` which keeps things cleaner.

Obviously this is a free repo with intention to have fun with a common Redis server, so it does not come with security-first principles!

Note the `SOUNDFONT` variable. This will allow you to load a soundfont file to be used for music in the game. If you don't want sound leave this empty

The script will load these variables both for the game code and the backend to read

3.  **Run the project via single script**

From the root directory run the script:

```
chmod +x build/start.sh
./build/start.sh

```

This will:

-   Build the Doom game

-   Set up backend (Python server)

-   Set up frontend (React UI)

-   Launch everything in proper order

* * * * *

Build manually (no script)
-----------

If you wish to run everything individually you should:

1.  **Compile the Doom game**
```
cd game-code/build
cmake ..
make
```
This will generate the `redis-doom` binary inside `game-code/build`

2.  **Setup the backend**
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

3.  **Setup frontend**
```
cd frontend

# Install node modules (only once)
npm install

# Start the React development server
npm start
```

4.  **Populate env variables via export**

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

You need to export at least the `PLAYER_PASSWORD` if you change it
e.g.
```
export PLAYER_PASSWORD=TestPassword
```

You can also export `PLAYER_NAME` or set it as parameter in the command line as shown below

5.  **Run the game**
```
cd game-code/build

# Replace DOOM.WAD with your WAD filename if different, and optionally add -playerName
# if not already set in .env
./redis-doom -iwad ../WADs/freedoom1.wad -playerName DoomSlayer
```

* * * * *

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

* * * * *

Tests
-------

Currently tested on MacOS environment only

* * * * *

License
-------

-   The original Doom source code is under **GPL v2**.

-   This project adds new code under the **MIT License**.

-   Game assets use [Freedoom](https://freedoom.github.io/) (BSD-like license).

* * * * *

Credits
-------

-   Doom source: id Software

-   Freedoom assets: Freedoom Project

-   Hiredis: RedisLabs

-   SDL2-Doom repo (https://github.com/AlexOberhofer/sdl2-doom)

* * * * *

Note
-------

This repo is just for fun and to play around with friends. 
It does not take into account things like session management and other mechanisms
that might matter in online games that share stats.

Anyway, happy playing and feel free to suggest additions that will make it more fun!