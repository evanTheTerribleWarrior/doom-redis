#!/bin/bash

set -e

if [ "$(uname)" != "Darwin" ]; then
  echo "[Error] This script is intended for macOS only."
  exit 1
fi

# Load environment variables
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

mkdir -p "$BUILD_DIR"

trap cleanup EXIT SIGINT SIGTERM

cleanup() {
  echo "[Cleanup] Killing any running processes..."
  pkill -f "python3 app.py" || true
  pkill -f "npm start" || true
  pkill -f "redis-doom" || true
  echo "[Cleanup] Cleaning up ports..."
  bash $BUILD_DIR/clean-ports.sh || true
}

wait_for_port() {
  PORT=$1
  echo "[Wait] Waiting for port $PORT to be available..."
  until python3 -c "import socket; s=socket.socket(); s.settimeout(0.5); s.connect(('localhost',$PORT))" >/dev/null 2>&1; do
    sleep 0.5
  done
  echo "[Wait] Port $PORT is now open!"
}

# Install Homebrew if missing
if ! command -v brew >/dev/null 2>&1; then
  echo "[Deps] Homebrew not found. Installing..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Install required packages
REQUIRED_BREW_PKGS=(cmake sdl2 sdl2_mixer python3)
for pkg in "${REQUIRED_BREW_PKGS[@]}"; do
  if ! brew list "$pkg" >/dev/null 2>&1; then
    echo "[Deps] Installing $pkg via Homebrew..."
    brew install "$pkg"
  else
    echo "[Deps] $pkg is already installed."
  fi
done

# Build hiredis
if [ ! -f "$HIREDIS_DIR/libhiredis.a" ]; then
  echo "[Deps] Cloning and building hiredis..."
  mkdir -p "$ROOT_DIR/deps"
  git clone https://github.com/redis/hiredis.git "$HIREDIS_DIR"
  cd "$HIREDIS_DIR"
  make -j$(sysctl -n hw.ncpu)
  cd "$ROOT_DIR"
else
  echo "[Deps] hiredis already built at $HIREDIS_DIR"
fi

# Build the game
mkdir -p "$GAME_BUILD_DIR"
find "$GAME_BUILD_DIR" -mindepth 1 -delete
cd "$GAME_BUILD_DIR"
cmake ..
make || { echo "[Error] Game build failed. Check $LOG_FILE"; exit 1; }
cd "$ROOT_DIR"

# Start backend
cd "$BACKEND_DIR"
if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
  rm -rf venv
  python3 -m venv venv || { echo "[Error] Failed to create venv"; exit 1; }
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python3 app.py &
BACKEND_PID=$!
wait_for_port 5000

# Start frontend
if ! command -v npm >/dev/null 2>&1; then
  echo "[Error] npm not found. Please install Node.js with: brew install node"
  exit 1
fi
cd "$FRONTEND_DIR"
npm install
npm start &
FRONTEND_PID=$!
wait_for_port 3000

# Start game
cd "$GAME_BUILD_DIR"
SOUNDFONT_PATH="$ROOT_DIR/game-code/soundfont/$SOUNDFONT"
export SDL_SOUNDFONTS="$SOUNDFONT_PATH"
./redis-doom -iwad "$WAD_DIR/$WAD_NAME" -playername "$PLAYER_NAME"
} 2>&1 | tee "$LOG_FILE"