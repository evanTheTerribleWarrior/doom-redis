DOOM Redis Edition
==================

Play Doom with a live Web UI showing real-time game stats, leaderboards, and chat --- powered by Redis Streams and WebSockets.

![Image](https://github.com/user-attachments/assets/a97bd1cf-cfb2-4185-b1fe-5703b738259c)

* * * * *

Current Features
--------

-   Live player chat feed (Redis Streams)

-   Live game event log feed (Redis Streams)

-   Real-time leaderboards and per-map domination tracking (Redis Streams)

-   Real-time in-game notifications (Redis PubSub)

* * * * *

Work in Progress
--------

-   More cases of in-game notifications
-   Per-WAD data separation
-   Looking for other cool ideas!

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

Modify `.env` if you are using an external Redis:

```
REDIS_HOST=<redis domain>
REDIS_PORT=<redis port>
REDIS_PASSWORD=<redis password>
SOUNDFONT=<soundfont file>

```

Note the `SOUNDFONT` variable. This will allow you to load a soundfont file to be used for music in the game. If you don't want sound leave this empty

The script will load these variables both for the game code and the backend to read

3.  **Run the project via single script**

Currently you need to do the following minimum configuration to define the Player Name and WAD in the `build/start.sh` script. Replace with your own values as needed

```
# Configuration
PLAYER_NAME="Doomslayer"
WAD_NAME="freedoom1.wad"
```

And then to run everything at once run the script:

```
chmod +x start.sh
./start.sh

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

4.  **Launch the game**
```
cd game-code/build

# Replace DOOM.WAD with your WAD filename if different
./redis-doom -iwad ../WADs/freedoom1.wad -playerName DoomSlayer
```

5.  **Redis Setup (Reminder)**

Make sure your Redis server is running before you launch the backend. You can either:

Run a local Redis server (redis-server) or

Connect to an external Redis as configured in your .env

If ports 5000 (backend) or 3000 (frontend) are occupied, you can manually kill them or use the provided `build/clean-ports.sh` script.

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
```

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

For example, if I start the game with another player's name, it will add stats to that player.
So if you want a proper management and isolation of each player you would need to
add that logic.

But who would want to ruin the fun??

Anyway, happy playing and feel free to suggest additions that will make it more fun!