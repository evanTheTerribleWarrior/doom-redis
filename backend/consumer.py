import redis
import time
import numpy as np
import uuid
import os
from redis.commands.search.field import TagField, VectorField, TextField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from achievements import KILL_STREAK_ACHIEVEMENTS, KILL_STREAK_BADGE_DEFINITIONS


# General players key
PLAYERS_KEY = 'doom:players'

# General WADs key (per-WAD data generation)
WADS_KEY = 'doom:wads'

# Stream and Consumer Group Definitions
EVENT_STREAM = 'doom:events'
CHAT_STREAM = 'doom:chat'

EVENT_GROUP = 'doom_event_consumer_group'
CHAT_GROUP = 'doom_chat_consumer_group'

EVENT_CONSUMER = 'doom_event_consumer'
CHAT_CONSUMER = 'doom_chat_consumer'

# Broadcast / PubSub
BROADCAST_CHANNEL = 'doom:players:broadcast'

# Vector Search indexes
SPREE_INDEX_NAME = f"doom:ai:vectors:sprees:idx"
SPREE_DOC_PREFIX = f"doom:ai:vectors:sprees:"
NOTIFICATION_EXPIRY = 10

# Checks if value is string or bytes and decodes accordingly
def safe_decode(value):
    if isinstance(value, bytes):
        return value.decode()
    elif isinstance(value, str):
        return value
    else:
        return ''

# For every incoming event we check if the player is on killing spree
# to push later as in-game notification
def check_kill_spree(player, streak):
    streak = int(streak)
    bit = KILL_STREAK_ACHIEVEMENTS.get(streak)
    label = KILL_STREAK_BADGE_DEFINITIONS.get(streak)['label']

    if bit is not None:
        return {
            "bit": bit,
            "message": f"{player} {streak} kill spree: {label}"
        }
    return None
    
# Mapping for killing spree, used to search if players had sprees
# in the area that player is currently in using similarity search
def get_vector_mapping(player, weapon, mapname, wadId, posX, posY):

    vec = np.array([posX, posY], dtype=np.float32).tobytes()

    return {
        'weapon': weapon,
        'player': player,
        'wadId': wadId,
        'mapname': mapname,
        'vector': vec
    }

def create_vss_index_spree(r):
                                
    try:
        r.ft(SPREE_INDEX_NAME).info()
        print(f"Index with name {SPREE_INDEX_NAME} already exists! Not creating again")
    except:
        schema = (
            TagField("wadId"), 
            TextField("weapon"),
            TextField("player"),  
            TextField("mapname"),                 
            VectorField("vector",               
                "FLAT", {                          
                    "TYPE": "FLOAT32",             
                    "DIM": 2,     
                    "DISTANCE_METRIC": "COSINE",
                }
            ),
        )

        definition = IndexDefinition(prefix=[SPREE_DOC_PREFIX], index_type=IndexType.HASH)
        r.ft(SPREE_INDEX_NAME).create_index(fields=schema, definition=definition)

# Creating all consumer groups as needed
def create_consumer_groups(r):
    for stream, group in [(EVENT_STREAM, EVENT_GROUP), (CHAT_STREAM, CHAT_GROUP)]:
        try:
            r.xgroup_create(stream, group, id='0', mkstream=True)
            print(f"[Redis] Created consumer group '{group}' for stream '{stream}'")
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                print(f"[Redis] Consumer group '{group}' already exists for stream '{stream}'")
            else:
                raise

# The main consumer for all event types like kills, shots etc
def start_event_consumer(r, socketio, enable_vectors):
    print("[Consumer] Starting Event Consumer...")

    # We create any indexes we need regardless of user enabling vector search
    # If index exists, nothing gets created
    create_vss_index_spree(r)

    while True:
        try:
            entries = r.xreadgroup(
                groupname=EVENT_GROUP,
                consumername=EVENT_CONSUMER,
                streams={EVENT_STREAM: '>'},
                count=100,
                block=0
            )

            for stream_key, events in entries:
                for event_id, data in events:
                    try:
                        player = safe_decode(data.get(b'playerName'))
                        weapon = safe_decode(data.get(b'weaponName', b'unknown'))
                        mapname = safe_decode(data.get(b'mapName', b'unknown'))
                        type = safe_decode(data.get(b'type', b'unknown'))
                        target = safe_decode(data.get(b'targetName', b''))
                        wadId = safe_decode(data.get(b'wadId', b''))

                        # We get the WAD filename to show it in the frontend
                        wad_filename = r.hget("doom:wads:wad-names", wadId)
                        if wad_filename:
                            wad_filename = wad_filename.decode()
                        else:
                            wad_filename = "unknown.wad"

                        if not player:
                            print(f"[Warning] Missing playerName in event {event_id}")
                            r.xack(EVENT_STREAM, EVENT_GROUP, event_id)
                            continue

                        if type == 'joined':
                            r.publish(BROADCAST_CHANNEL, f"{player} joined the game")
                            r.xack(EVENT_STREAM, EVENT_GROUP, event_id)
                            continue
                        
                        # If user enabled the ENABLE_VECTOR variable
                        # We get their current position and create a query vector to check
                        # if there are prior killing sprees nearby to send them weapon recommendation
                        # We also check if we should send the notification as we don't want to send too frequently
                        if enable_vectors:
                            if type == 'movement': 
                                posX = safe_decode(data.get(b'posX', b''))
                                posY = safe_decode(data.get(b'posY', b''))
                                notification_key = f"doom:ai:notification:sent:{player}"

                                if not r.exists(notification_key):
                                    query_vec = np.array([float(posX), float(posY)], dtype=np.float32).tobytes()
                                    res = r.ft(SPREE_INDEX_NAME).search(
                                        Query("*=>[KNN 1 @vector $vec]").paging(0, 1).return_fields("weapon", "player", "wadId", "mapname", "vector").dialect(2),
                                        {"vec": query_vec}
                                    )
                                    if res.total > 0:
                                        match = res.docs[0]
                                        if match.player != player:
                                            if(match.wadId == wadId and match.mapname == mapname):
                                                r.publish(f"doom:player:{player}", f"Recommended Weapon here: {match.weapon}")
                                                r.set(notification_key, value="1",ex=NOTIFICATION_EXPIRY)


                        log_msg = None
                        pipe = r.pipeline()

                        # Base player key paths
                        player_total = f'{PLAYERS_KEY}:{player}:total-stats'
                        wad_player = f'{WADS_KEY}:stats:{wadId}:players:{player}'
                        wad_map_player = f'{WADS_KEY}:stats:{wadId}:maps:{mapname}:{player}'

                        if type == 'kill':
                            log_msg = f"[{wad_filename}]: {player} killed {target or 'an enemy'} with a {weapon} on {mapname}"

                            r.incrby(f'{PLAYERS_KEY}:{player}:streak', 1)
                            streak = r.get(f'{PLAYERS_KEY}:{player}:streak')

                            # We check if the player has a kill spree and if so
                            # we add their current coordinates and other details to a vector
                            # to be used later in Vector Searches
                            kill_spree = check_kill_spree(player, streak)
                            if kill_spree is not None:
                                posX = safe_decode(data.get(b'posX', b''))
                                posY = safe_decode(data.get(b'posY', b''))
                                vector_mapping = get_vector_mapping(player, weapon, mapname, wadId, float(posX), float(posY))
                                spree_id = str(uuid.uuid4())
                                key = f'doom:ai:vectors:sprees:{spree_id}'
                                pipe.hset(key, mapping = vector_mapping)

                                # Update the kill spree achievement BITFIELD and publish notification
                                pipe.setbit(f"doom:achievements:{player}", kill_spree["bit"], 1)
                                pipe.publish(BROADCAST_CHANNEL, kill_spree["message"])

                            pipe.hincrby(player_total, 'totalKills', 1)
                            pipe.hincrby(wad_player, 'totalKills', 1)
                            pipe.hincrby(wad_map_player, 'totalKills', 1)

                        elif type == 'death':
                            log_msg = f"[{wad_filename}]: {player} WAS KILLED by {target or 'something'}"
                            pipe.hincrby(player_total, 'totalDeaths', 1)
                            pipe.hincrby(wad_player, 'totalDeaths', 1)
                            pipe.hincrby(wad_map_player, 'totalDeaths', 1)
                            pipe.set(f'{PLAYERS_KEY}:{player}:streak', "0")
                            pipe.publish(BROADCAST_CHANNEL, log_msg)

                        elif type == 'shot':
                            pipe.hincrby(player_total, 'totalShots', 1)
                            pipe.hincrby(wad_player, 'totalShots', 1)
                            pipe.hincrby(wad_map_player, 'totalShots', 1)
                            pipe.hincrby(f'{PLAYERS_KEY}:{player}:weapons', weapon, 1)

                        # Compute efficiency and update WAD-specific leaderboards
                        kills = int(r.hget(wad_player, 'totalKills') or 0)
                        shots = int(r.hget(wad_player, 'totalShots') or 0)
                        efficiency = round(kills / shots, 4) if shots > 0 else 0.0

                        # Add values for leaderboard and timeseries
                        pipe.zadd(f'{WADS_KEY}:stats:{wadId}:leaderboard:scores', {player: kills})
                        pipe.zadd(f'{WADS_KEY}:stats:{wadId}:leaderboard:efficiency', {player: efficiency})
                        pipe.ts().add(f'{WADS_KEY}:stats:{wadId}:timeseries:{player}:efficiency', '*', efficiency)
                        
                        # Track all players for this WAD
                        pipe.sadd(f'{WADS_KEY}:stats:{wadId}:players', player)

                        socketio.emit('leaderboard:update', {"wadId": wadId})
                        if log_msg:
                            socketio.emit('gamelog:update', {"log_msg": log_msg})
                        
                        socketio.emit('efficiency:update', { "player": player, "wadId": wadId })

                        pipe.execute()
                        r.xack(EVENT_STREAM, EVENT_GROUP, event_id)

                    except Exception as e:
                        print(f"[Error] Failed to process event {event_id}: {e}")
                        r.xack(EVENT_STREAM, EVENT_GROUP, event_id)

        except redis.exceptions.ConnectionError as e:
            print(f"[Redis] Connection error: {e}")
            time.sleep(1)

# Main consumer for real-time chat events
# All chat events are pushed via websocket to the frontend
# and also as in-game notifications
def start_chat_consumer(r, socketio):
    print("[Consumer] Starting Chat Consumer...")

    while True:
        try:
            entries = r.xreadgroup(
                groupname=CHAT_GROUP,
                consumername=CHAT_CONSUMER,
                streams={CHAT_STREAM: '>'},
                count=100,
                block=0
            )

            for stream_key, events in entries:
                for event_id, data in events:
                    try:
                        raw_player = data.get(b'playerName')
                        raw_message = data.get(b'message')

                        player = safe_decode(raw_player)
                        message = safe_decode(raw_message)

                        if player and message:
                            chat_msg = f"[{player}]: {message}"
                            socketio.emit('chat:update', {'chat_msg': chat_msg})
                            r.publish(BROADCAST_CHANNEL, chat_msg)

                        r.xack(CHAT_STREAM, CHAT_GROUP, event_id)
                        print(f"[Redis] Acknowledged Chat {event_id}")

                    except Exception as e:
                        print(f"[Error] Failed to process chat {event_id}: {e}")
                        r.xack(CHAT_STREAM, CHAT_GROUP, event_id)

        except redis.exceptions.ConnectionError as e:
            print(f"[Redis] Connection error: {e}")
            time.sleep(1)
