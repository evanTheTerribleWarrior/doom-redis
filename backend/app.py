import eventlet
eventlet.monkey_patch()
from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import redis
import os

from dotenv import load_dotenv
load_dotenv()

from consumer import (
    create_consumer_groups,
    start_event_consumer,
    start_chat_consumer
)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
CORS(app)

redis_host = os.getenv('REDIS_HOST')
if(redis_host == ""):
    redis_host = 'localhost'
redis_port = os.getenv('REDIS_PORT')
if(redis_port == ""):
    redis_port = 6379
redis_password = os.getenv('REDIS_PASSWORD')
if(redis_password == ""):
    redis_password = None

r = redis.Redis(
    host=redis_host,
    port=redis_port,
    password=redis_password,
    decode_responses=False
)


@app.route('/api/load_logs')
def load_logs():
    entries = r.xrevrange('doom:events', count=100)
    logs = []
    for _, data in reversed(entries):
        player = data.get(b'playerName', b'').decode()
        weapon = data.get(b'weaponName', b'unknown').decode()
        mapname = data.get(b'mapName', b'unknown').decode()
        type = data.get(b'type', b'unknown').decode()
        target = data.get(b'targetName', b'').decode()

        log_msg = None
        if type == 'kill':
            log_msg = f"Player {player} killed {target or 'an enemy'} with a {weapon} on {mapname}"
        elif type == 'death':
            log_msg = f"Player {player} WAS KILLED by {target or 'something'} on {mapname}"

        if log_msg:
            logs.append(log_msg)

    return jsonify(logs)

@app.route('/api/load_chat')
def load_chat():
    entries = r.xrevrange('doom:chat', count=100)
    chats = []
    for _, data in reversed(entries):
        player = data.get(b'playerName', b'').decode()
        message = data.get(b'message', b'').decode()
        if player and message:
            chats.append(f"{player}: {message}")

    return jsonify(chats)

@app.route('/api/leaderboard')
def leaderboard():
    players = r.smembers('doom:players')
    data = []

    for p in players:
        name = p.decode()
        stats = r.hgetall(f'doom:players:{name}:total-stats')
        kills = int(stats.get(b'totalKills', 0))
        shots = int(stats.get(b'totalShots', 0))
        deaths = int(stats.get(b'totalDeaths', 0))
        efficiency = round(kills / shots, 2) if shots > 0 else 0

        weapon_stats = r.hgetall(f'doom:players:{name}:weapons')
        preferred_weapon = "unknown"
        if weapon_stats:
            preferred_weapon = max(weapon_stats.items(), key=lambda x: int(x[1]))[0].decode()

        data.append({
            'player': name,
            'kills': kills,
            'shots': shots,
            'deaths': deaths,
            'efficiency': efficiency,
            'preferredWeapon': preferred_weapon
        })

    return jsonify(data)

@app.route('/api/map-leaderboard')
def map_leaderboard():
    players = r.smembers('doom:players')
    map_stats = {}

    for p in players:
        name = p.decode()
        for key in r.scan_iter(f"doom:players:{name}:map:*"):
            _, _, player, _, mapname = key.decode().split(':')
            stats = r.hgetall(key)
            kills = int(stats.get(b'totalKills', 0))
            shots = int(stats.get(b'totalShots', 0))
            efficiency = round(kills / shots, 2) if shots > 0 else 0

            if mapname not in map_stats or map_stats[mapname]['kills'] < kills:
                map_stats[mapname] = {
                    'map': mapname,
                    'topPlayer': name,
                    'kills': kills,
                    'efficiency': efficiency
                }

    return jsonify(list(map_stats.values()))

if __name__ == '__main__':
    create_consumer_groups(r) 
    socketio.start_background_task(start_event_consumer, r, socketio)
    socketio.start_background_task(start_chat_consumer, r, socketio)
    socketio.run(app, allow_unsafe_werkzeug=True)
