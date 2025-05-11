import eventlet
eventlet.monkey_patch()
from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import redis
import os
from flask import request
import time
from achievements import KILL_STREAK_ACHIEVEMENTS, KILL_STREAK_BADGE_DEFINITIONS



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


# We get the WAD names based on the extracted WAD IDs from the game source code
# This is used to present a proper friendly name instead of ID
@app.route('/api/wads/wadnames')
def load_wadnames():
    wad_map = r.hgetall('doom:wads:wad-names')
    result = []

    for wadId, name in wad_map.items():
        result.append({
            'id': wadId.decode(),
            'name': name.decode()
        })

    result.sort(key=lambda x: x['name'].lower())
    return jsonify(result)

# Used to pull the last 100 lines of logs
# Triggered from the websocket as new logs arrive
@app.route('/api/load_logs')
def load_logs():
    entries = r.xrevrange('doom:events', count=100)
    logs = []

    wad_name_cache = {}

    for _, data in reversed(entries):
        player = data.get(b'playerName', b'').decode()
        weapon = data.get(b'weaponName', b'unknown').decode()
        mapname = data.get(b'mapName', b'unknown').decode()
        type = data.get(b'type', b'unknown').decode()
        target = data.get(b'targetName', b'').decode()
        wadId = data.get(b'wadId', b'').decode()

        if wadId:
            if wadId not in wad_name_cache:
                wad_name = r.hget("doom:wads:wad-names", wadId)
                wad_name_cache[wadId] = wad_name.decode() if wad_name else "unknown.wad"
            wad_filename = wad_name_cache[wadId]
        else:
            wad_filename = "unknown.wad"

        log_msg = None
        if type == 'kill':
            log_msg = f"[{wad_filename}]: Player {player} killed {target or 'an enemy'} with a {weapon} on {mapname}"
        elif type == 'death':
            log_msg = f"[{wad_filename}]: Player {player} WAS KILLED by {target or 'something'} on {mapname}"

        if log_msg:
            logs.append(log_msg)

    return jsonify(logs)

# Used to pull last 100 chat messages in the UI
# Triggered by the websocket every time new message arrives
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
    wadID = request.args.get('wadId')
    if not wadID:
        return jsonify({'error': 'Missing wadId'}), 400

    leaderboard_key = f'doom:wads:stats:{wadID}:leaderboard:efficiency'
    leaderboard_data = r.zrevrange(leaderboard_key, 0, -1, withscores=True)

    data = []

    for player, efficiency in leaderboard_data:
        player = player.decode()
        stats_key = f'doom:wads:stats:{wadID}:players:{player}'
        weapon_key = f'doom:players:{player}:weapons'

        stats = r.hgetall(stats_key)
        kills = int(stats.get(b'totalKills', 0))
        shots = int(stats.get(b'totalShots', 0))
        deaths = int(stats.get(b'totalDeaths', 0))

        weapon_stats = r.hgetall(weapon_key)
        preferred_weapon = "unknown"
        if weapon_stats:
            preferred_weapon = max(weapon_stats.items(), key=lambda x: int(x[1]))[0].decode()

        data.append({
            'player': player,
            'kills': kills,
            'shots': shots,
            'deaths': deaths,
            'efficiency': round(efficiency, 2),
            'preferredWeapon': preferred_weapon
        })

    return jsonify(data)

@app.route('/api/map-leaderboard')
def map_leaderboard():
    wadID = request.args.get('wadId')
    if not wadID:
        return jsonify({'error': 'Missing wadId'}), 400
    
    map_stats = {}
    prefix = f'doom:wads:stats:{wadID}:maps:'

    for key in r.scan_iter(f'{prefix}*'):
        key_parts = key.decode().split(':')
        if len(key_parts) < 7:
            continue

        mapname = key_parts[5]
        player = key_parts[6]

        stats = r.hgetall(key)
        kills = int(stats.get(b'totalKills', 0))
        shots = int(stats.get(b'totalShots', 0))
        efficiency = round(kills / shots, 2) if shots > 0 else 0

        current = map_stats.get(mapname)
        if current is None or kills > current['kills']:
            map_stats[mapname] = {
                'map': mapname,
                'topPlayer': player,
                'kills': kills,
                'efficiency': efficiency
            }

    return jsonify(list(map_stats.values()))


# Gives a full list of player names based on the Redis Set
# Useful for PerformanceTracker component and anywhere else it might be needed
@app.route('/api/players')
def get_players():
    players = r.smembers('doom:players')
    player_names = [p.decode() if isinstance(p, bytes) else p for p in players]
    return jsonify(player_names)

# Searches the players based on what the user is typing
@app.route('/api/search_players')
def search_players():
    query = request.args.get('q', '')
    suggestions = r.ft().sugget(
        key="doom:player-search",
        prefix=query,
    )
    results = [s.string for s in suggestions]
    return jsonify(results)

# Get stats per user. Useful for PlayerSearch
@app.route('/api/player/<player_name>')
def player_stats(player_name):
    stats_key = f'doom:players:{player_name}:total-stats'
    weapon_key = f'doom:players:{player_name}:weapons'
    achievement_key = f'doom:achievements:{player_name}'

    if not r.exists(stats_key):
        return jsonify({'error': 'Player not found'}), 404

    stats = r.hgetall(stats_key)
    kills = int(stats.get(b'totalKills', 0))
    shots = int(stats.get(b'totalShots', 0))
    deaths = int(stats.get(b'totalDeaths', 0))
    efficiency = round(kills / shots, 2) if shots > 0 else 0.0

    weapon_stats = r.hgetall(weapon_key)
    preferred_weapon = "unknown"
    if weapon_stats:
        preferred_weapon = max(weapon_stats.items(), key=lambda x: int(x[1]))[0].decode()

    achievements = []
    for streak, bit in KILL_STREAK_ACHIEVEMENTS.items():
        if r.getbit(achievement_key, bit):
            defn = KILL_STREAK_BADGE_DEFINITIONS.get(streak)
            if defn:
                achievements.append({
                    "key": defn["key"],
                    "description": defn["description"],
                    "label": defn["label"]
                })

    return jsonify({
        'player': player_name,
        'kills': kills,
        'shots': shots,
        'deaths': deaths,
        'efficiency': efficiency,
        'preferredWeapon': preferred_weapon,
        'achievements': achievements 
    })

# Provides the timeseries value for the player. The range can be changed
# depending how long back we want to look
@app.route('/api/player/<player_name>/efficiency_timeseries')
def player_timeseries(player_name):

    wadID = request.args.get('wadId')
    if not wadID:
        return jsonify({'error': 'Missing wadId'}), 400

    key = f'doom:wads:stats:{wadID}:timeseries:{player_name}:efficiency'
    print(key)
    try:
        now = int(time.time() * 1000)
        one_week_ago = now - (7 * 24 * 60 * 60 * 1000)
        points = r.ts().range(key, from_time=one_week_ago, to_time=now)

        result = [
            {
                "timestamp": time.strftime('%Y-%m-%d %H:%M', time.localtime(int(ts) / 1000)),
                "efficiency": float(val)
            }
            for ts, val in points
        ]

        return jsonify(result)
    except Exception as e:
        print(f"[Error] TS.RANGE for {player_name}: {e}")
        return jsonify([]), 500

if __name__ == '__main__':
    create_consumer_groups(r) 
    enable_vectors = os.getenv("ENABLE_VECTOR", "0") == "1"
    socketio.start_background_task(start_event_consumer, r, socketio, enable_vectors)
    socketio.start_background_task(start_chat_consumer, r, socketio)
    socketio.run(app, allow_unsafe_werkzeug=True)
