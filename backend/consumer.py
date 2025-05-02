import redis
import time

# Stream and Consumer Group Definitions
EVENT_STREAM = 'doom:events'
CHAT_STREAM = 'doom:chat'

EVENT_GROUP = 'doom_event_consumer_group'
CHAT_GROUP = 'doom_chat_consumer_group'

EVENT_CONSUMER = 'doom_event_consumer'
CHAT_CONSUMER = 'doom_chat_consumer'

# Broadcast / PubSub
BROADCAST_CHANNEL = 'doom:players:broadcast'

def safe_decode(value):
    if isinstance(value, bytes):
        return value.decode()
    elif isinstance(value, str):
        return value
    else:
        return ''

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

def start_event_consumer(r, socketio):
    print("[Consumer] Starting Event Consumer...")

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

                        if not player:
                            print(f"[Warning] Missing playerName in event {event_id}")
                            r.xack(EVENT_STREAM, EVENT_GROUP, event_id)
                            continue

                        log_msg = None

                        if type == 'kill':
                            log_msg = f"{player} killed {target or 'an enemy'} with a {weapon} on {mapname}"
                            r.hincrby(f'doom:player:{player}', 'totalKills', 1)
                            r.hincrby(f'doom:player:{player}:map:{mapname}', 'totalKills', 1)
                            r.zincrby('doom:leaderboard:kills', 1, player)
                            #r.publish('doom:players:broadcast', log_msg)

                        elif type == 'death':
                            log_msg = f"{player} WAS KILLED by {target or 'something'}"
                            r.hincrby(f'doom:player:{player}', 'totalDeaths', 1)
                            r.hincrby(f'doom:player:{player}:map:{mapname}', 'totalDeaths', 1)
                            r.publish(BROADCAST_CHANNEL, log_msg)

                        elif type == 'shot':
                            log_msg = f"{player} fired a {weapon} on {mapname}"
                            r.hincrby(f'doom:player:{player}', 'totalShots', 1)
                            r.hincrby(f'doom:player:{player}:map:{mapname}', 'totalShots', 1)
                            r.hincrby(f'doom:player:{player}:weapons', weapon, 1)

                        # Always update efficiency after any event
                        kills = int(r.hget(f'doom:player:{player}', 'totalKills') or 0)
                        shots = int(r.hget(f'doom:player:{player}', 'totalShots') or 0)
                        efficiency = round(kills / shots, 4)
                        r.zadd('doom:leaderboard:efficiency', {player: efficiency})

                        if log_msg:
                            socketio.emit('leaderboard:update', {'log_msg': log_msg})
                            socketio.emit('gamelog:update', {'log_msg': log_msg})

                        r.xack(EVENT_STREAM, EVENT_GROUP, event_id)

                    except Exception as e:
                        print(f"[Error] Failed to process event {event_id}: {e}")
                        r.xack(EVENT_STREAM, EVENT_GROUP, event_id)

        except redis.exceptions.ConnectionError as e:
            print(f"[Redis] Connection error: {e}")
            time.sleep(1)

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

                        print(f"[Debug] Decoded player='{player}', message='{message}'")    

                        if player and message:
                            chat_msg = f"[{player}]: {message}"
                            print("Sending message to frontend: ", chat_msg)
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
