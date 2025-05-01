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

kill_port 5000
kill_port 3000