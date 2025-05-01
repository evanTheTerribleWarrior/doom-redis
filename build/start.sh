#!/bin/bash

set -e  # Stop immediately if any command fails

# Load .env file into environment
export $(grep -v '^#' .env | xargs)

ROOT_DIR="$(dirname "$(dirname "$(realpath "$0")")")"
BUILD_DIR="$ROOT_DIR/build"
LOG_FILE="$BUILD_DIR/build.log"

{
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
GAME_DIR="$ROOT_DIR/game-code/src"
GAME_BUILD_DIR="$ROOT_DIR/game-code/build"
WAD_DIR="$ROOT_DIR/game-code/WADs"

# Configuration - change this to the values you want
PLAYER_NAME="DoomSlayer"
WAD_NAME="freedoom1.wad"

# Ensure build directory exists
mkdir -p "$BUILD_DIR"

# Trap to clean up on exit and Ctrl-C
trap cleanup EXIT SIGINT SIGTERM

cleanup() {
    echo "[Cleanup] Killing any running processes..."
    pkill -f "python3 app.py" || true
    pkill -f "npm start" || true
    pkill -f "redis-doom" || true

    echo "[Cleanup] Cleaning up ports..."
    bash $BUILD_DIR/clean-ports.sh || true
}

# Function to check and kill processes on a port
kill_port() {
  PORT=$1
  PID_ON_PORT=$(lsof -ti tcp:$PORT)

  if [ ! -z "$PID_ON_PORT" ]; then
    echo "[Build] Port $PORT is already in use by PID(s): $PID_ON_PORT. Killing them..."
    for pid in $PID_ON_PORT; do
      echo "[Build] Killing PID $pid on port $PORT..."
      kill -9 "$pid"
    done
    sleep 2
  fi
}

# Function to wait until a port is open
wait_for_port() {
  PORT=$1
  echo "[Wait] Waiting for port $PORT to be available..."
  while ! nc -z localhost $PORT; do
    sleep 0.5
  done
  echo "[Wait] Port $PORT is now open!"
}

echo "[Step 1] Building the game..."

if [ ! -d "$GAME_BUILD_DIR" ]; then
  echo "[Init] Creating missing build directory: $GAME_BUILD_DIR"
  mkdir -p "$GAME_BUILD_DIR"
fi

find "$GAME_BUILD_DIR" -mindepth 1 -delete
cd "$GAME_BUILD_DIR"
cmake ..
make || { echo "[Error] Game build failed. Check $LOG_FILE"; exit 1; }
cd "$ROOT_DIR"

# Start Backend
echo "[Step 2] Starting backend..."
cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
    echo "[Build] Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

python3 app.py &
BACKEND_PID=$!
wait_for_port 5000

echo "[Build] Backend running with PID $BACKEND_PID"

# Start Frontend
echo "[Step 3] Starting frontend..."
cd "$FRONTEND_DIR"
npm install

npm start &
FRONTEND_PID=$!
wait_for_port 3000

echo "[Build] Frontend running with PID $FRONTEND_PID"

# Launch Doom
echo "[Step 4] Launching Doom game..."
cd "$GAME_BUILD_DIR"

SOUNDFONT_PATH="$ROOT_DIR/game-code/soundfont/$SOUNDFONT"
export SDL_SOUNDFONTS="$SOUNDFONT_PATH"
echo "[Sound] Using SoundFont at $SOUNDFONT_PATH"

./redis-doom -iwad "$WAD_DIR/$WAD_NAME" -playerName "$PLAYER_NAME"

DOOM_PID=$!

echo "[Build] All components launched successfully!"

} 2>&1 | tee "$LOG_FILE"