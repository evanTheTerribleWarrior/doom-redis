DOOM Redis Edition
==================

Play Doom with a live Web UI showing real-time game stats, leaderboards, and chat --- powered by Redis Streams and WebSockets.

![Image](https://github.com/user-attachments/assets/e292422a-ca25-4f60-a5e1-b1bf1960e262)

* * * * *

Features
--------

-   Play Doom with a Redis-powered backend

-   Live player chat feed

-   Live game event log feed (shots, kills, deaths)

-   Real-time leaderboards (kills, efficiency)

-   Per-map domination tracking

-   Smooth WebSocket updates (no refresh needed)

![Gameplay](https://github.com/user-attachments/assets/9a344564-1b1e-4986-b0cd-efc62bee07db)

Includes in-game chat (using Redis Streams)
![Chat](https://github.com/user-attachments/assets/008f0079-5cd9-46e6-9d0a-0e06e703a629)

* * * * *

Project Structure
-----------------

```
/
├── WADs/              # Contains the game WAD files (e.g., freedoom1.wad)
├── backend/           # Python Flask + Socket.IO server (real-time event broadcasting)
├── frontend/          # React-based frontend UI (game logs, player chat, leaderboards)
├── game-code/         # Original DOOM source code (modified for Redis integration)
├── hiredis-master/    # Local hiredis library (compiled during game build)
├── clean-ports.sh     # Optional script to free ports 5000/3000 manually
├── start.sh           # Main script: builds, runs backend/frontend, launches the game
├── README.md          # This file
└── .env               # Environment variables (Redis host, port, etc.)

```

* * * * *

Quick Start
-----------

Requirements:

-   Python 3.11+

-   Node.js + npm

-   Redis server (local or cloud)

-   Linux/macOS system

1.  **Clone the repository**

```
git clone https://github.com/your-username/doom-redis.git
cd doom-redis

```

1.  **Add a WAD file**

The repo comes with a downloaded version of Freedoom 1 & 2. 
You can find them under the `WADs` folder.

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

```

The script will load these variables both for the game code and the backend to read

3.  **Run the project via single script**

Currently you need to do the following minimum configuration to define the Player Name and WAD in the `start.sh` script. Replace with your own values as needed

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

If you wish to run everything individually you should:
1. Compile the Doom game
```
cd game-code/linuxdoom-1.10
make clean
make
```
This will generate the linuxxdoom binary inside `game-code/linuxdoom-1.10/linux/`

2. Setup the backend
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

3. Setup frontend
```
cd frontend

# Install node modules (only once)
npm install

# Start the React development server
npm start
```

4. Launch the game
```
cd game-code/linuxdoom-1.10/linux

# Replace DOOM.WAD with your WAD filename if different
./linuxxdoom -file ../../WADs/freedoom1.wad -playerName Doomslayer
```

5. Redis Setup (Reminder)

Make sure your Redis server is running before you launch the backend. You can either:

Run a local Redis server (redis-server) or

Connect to an external Redis as configured in your .env

If ports 5000 (backend) or 3000 (frontend) are occupied, you can manually kill them or use the provided `clean-ports.sh` script.

* * * * *

Project Architecture
--------------------

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

-   Thanks to all open-source contributors.

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