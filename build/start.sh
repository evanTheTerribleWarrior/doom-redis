#!/bin/bash

set -e  # Stop immediately if any command fails

# Load .env file into environment
set -o allexport
source ../.env
set +o allexport

ROOT_DIR="$(dirname "$(dirname "$(realpath "$0")")")"
BUILD_DIR="$ROOT_DIR/build"
LOG_FILE="$BUILD_DIR/build.log"

{
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
GAME_DIR="$ROOT_DIR/game-code/src"
GAME_BUILD_DIR="$ROOT_DIR/game-code/build"
WAD_DIR="$ROOT_DIR/game-code/WADs"
HIREDIS_DIR="$ROOT_DIR/deps/hiredis"

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

  until python3 -c "
import socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(0.5)
    try:
        s.connect(('localhost', $PORT))
    except:
        exit(1)
  " >/dev/null 2>&1; do
    sleep 0.5
  done

  echo "[Wait] Port $PORT is now open!"
}

# -----------------------------------------------------------------------------
# [Step 0] Install system dependencies (Linux/macOS)
# -----------------------------------------------------------------------------

echo "[Deps] Checking system dependencies..."

if [ "$(uname)" == "Darwin" ]; then
  echo "[System] macOS detected."

  REQUIRED_BREW_PKGS=(cmake sdl2 sdl2_mixer python3)

  for pkg in "${REQUIRED_BREW_PKGS[@]}"; do
    if ! brew list "$pkg" >/dev/null 2>&1; then
      echo "[Deps] Installing $pkg via Homebrew..."
      brew install "$pkg"
    else
      echo "[Deps] $pkg is already installed."
    fi
  done

elif [ -f /etc/debian_version ]; then
  echo "[System] Debian/Ubuntu detected."

  REQUIRED_PKGS=(
    cmake build-essential libsdl2-dev libsdl2-mixer-dev libhiredis-dev
    python3 python3-pip python3-venv git lsof
  )

  MISSING_PKGS=()

  for pkg in "${REQUIRED_PKGS[@]}"; do
    if ! dpkg -s $pkg >/dev/null 2>&1; then
      MISSING_PKGS+=($pkg)
    fi
  done

  if [ ${#MISSING_PKGS[@]} -ne 0 ]; then
    echo "[Deps] Installing missing packages: ${MISSING_PKGS[*]}"
    if [ "$EUID" -ne 0 ]; then
      echo "[Error] Run this script with sudo to install system packages."
      exit 1
    fi
    apt update && apt install -y "${MISSING_PKGS[@]}"
  else
    echo "[Deps] All required packages are installed."
  fi

else
  echo "[Warning] Unsupported OS: $(uname). You may need to install dependencies manually."
fi

# -----------------------------------------------------------------------------
# [Step 1] Build hiredis (local static version)
# -----------------------------------------------------------------------------

echo "[Step 1] Building hiredis..."

if [ ! -f "$HIREDIS_DIR/libhiredis.a" ]; then
  echo "[Deps] Cloning and building hiredis..."
  mkdir -p "$ROOT_DIR/deps"
  git clone https://github.com/redis/hiredis.git "$HIREDIS_DIR"
  cd "$HIREDIS_DIR"
  make -j$(nproc)
  cd "$ROOT_DIR"
else
  echo "[Deps] hiredis already built at $HIREDIS_DIR"
fi

# -----------------------------------------------------------------------------
# [Step 2] Build Doom game
# -----------------------------------------------------------------------------

echo "[Step 2] Building the game..."

if [ ! -d "$GAME_BUILD_DIR" ]; then
  echo "[Init] Creating missing build directory: $GAME_BUILD_DIR"
  mkdir -p "$GAME_BUILD_DIR"
fi

find "$GAME_BUILD_DIR" -mindepth 1 -delete
cd "$GAME_BUILD_DIR"
cmake ..
make || { echo "[Error] Game build failed. Check $LOG_FILE"; exit 1; }
cd "$ROOT_DIR"

# -----------------------------------------------------------------------------
# [Step 3] Start Backend
# -----------------------------------------------------------------------------

echo "[Step 3] Starting backend..."
cd "$BACKEND_DIR"

if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    echo "[Build] Creating Python virtual environment..."
    rm -rf venv  # remove any broken or partial venv
    if ! python3 -m venv venv; then
        echo "[Error] Failed to create virtualenv. Is python3-venv installed?"
        exit 1
    fi
fi

if [ ! -f "venv/bin/activate" ]; then
    echo "[Error] Python virtual environment was not created properly."
    exit 1
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

python3 app.py &
BACKEND_PID=$!
wait_for_port 5000

echo "[Build] Backend running with PID $BACKEND_PID"

# -----------------------------------------------------------------------------
# [Step 4] Start Frontend
# -----------------------------------------------------------------------------

if ! command -v npm >/dev/null 2>&1; then
  if [ -f /etc/debian_version ]; then
    echo "[Deps] Node.js and npm not found. Installing..."

    if [ "$EUID" -ne 0 ]; then
      echo "[Error] Please run with sudo to install Node.js on Debian/Ubuntu."
      exit 1
    fi

    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs

    echo "[Deps] Node.js $(node -v) and npm $(npm -v) installed."
  else
    echo "[Error] npm not found, and OS is not Debian-based. Install Node.js manually."
    exit 1
  fi
fi

echo "[Step 4] Starting frontend..."

cd "$FRONTEND_DIR"
npm install

npm start &
FRONTEND_PID=$!
wait_for_port 3000

echo "[Build] Frontend running with PID $FRONTEND_PID"

# -----------------------------------------------------------------------------
# [Step 5] Launch Doom Game
# -----------------------------------------------------------------------------

echo "[Step 5] Launching Doom game..."
cd "$GAME_BUILD_DIR"

SOUNDFONT_PATH="$ROOT_DIR/game-code/soundfont/$SOUNDFONT"
export SDL_SOUNDFONTS="$SOUNDFONT_PATH"
echo "[Sound] Using SoundFont at $SOUNDFONT_PATH"

./redis-doom -iwad "$WAD_DIR/$WAD_NAME" -playername "$PLAYER_NAME"

DOOM_PID=$!

echo "[Build] All components launched successfully!"

} 2>&1 | tee "$LOG_FILE"
