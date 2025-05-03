import redis
import time

# General players key
PLAYERS_KEY = 'doom:players'

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
    
def check_kill_spree(player, streak):

    status = None
    apply_spree = False

    streak = int(streak)

    if streak == 5:
        status = "AWESOME"
        apply_spree = True
    elif streak == 10:
        status = "DOMINATING"
        apply_spree = True
    elif streak == 15:
        status = "UNSTOPPABLE"
        apply_spree = True
    elif streak == 20:
        status = "LEGENDARY"
        apply_spree = True
    elif streak == 30:
        status = "TRUE SLAYER"
        apply_spree = True

    if apply_spree:
        return f"{player} {streak} kill spree: {status}"  
    else:
        return None  

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

                        if type == 'joined':
                            r.publish(BROADCAST_CHANNEL, f"{player} joined the game")
                            r.xack(EVENT_STREAM, EVENT_GROUP, event_id)
                            continue
                        
                        log_msg = None
                        pipe = r.pipeline()

                        if type == 'kill':
                            log_msg = f"{player} killed {target or 'an enemy'} with a {weapon} on {mapname}"

                            r.incrby(f'{PLAYERS_KEY}:{player}:streak', 1)
                            streak = r.get(f'{PLAYERS_KEY}:{player}:streak')
                            kill_spree = check_kill_spree(player, streak)
                            if kill_spree is not None:
                                pipe.publish(BROADCAST_CHANNEL, kill_spree)
                            
                            pipe.hincrby(f'{PLAYERS_KEY}:{player}:total-stats', 'totalKills', 1)
                            pipe.hincrby(f'{PLAYERS_KEY}:{player}:map:{mapname}', 'totalKills', 1)
                            pipe.zincrby('doom:leaderboard:kills', 1, player)
                            

                        elif type == 'death':
                            log_msg = f"{player} WAS KILLED by {target or 'something'}"
                            pipe.hincrby(f'{PLAYERS_KEY}:{player}:total-stats', 'totalDeaths', 1)
                            pipe.hincrby(f'{PLAYERS_KEY}:{player}:map:{mapname}', 'totalDeaths', 1)
                            pipe.set(f'{PLAYERS_KEY}:{player}:streak', "0")
                            pipe.publish(BROADCAST_CHANNEL, log_msg)

                        elif type == 'shot':
                            log_msg = f"{player} fired a {weapon} on {mapname}"
                            pipe.hincrby(f'{PLAYERS_KEY}:{player}:total-stats', 'totalShots', 1)
                            pipe.hincrby(f'{PLAYERS_KEY}:{player}:map:{mapname}', 'totalShots', 1)
                            pipe.hincrby(f'{PLAYERS_KEY}:{player}:weapons', weapon, 1)

                        # Always update efficiency after any event
                        kills = int(r.hget(f'{PLAYERS_KEY}:{player}:total-stats', 'totalKills') or 0)
                        shots = int(r.hget(f'{PLAYERS_KEY}:{player}:total-stats', 'totalShots') or 0)
                        if shots > 0:
                            efficiency = round(kills / shots, 4)
                        else:
                            efficiency = 0.0
                        pipe.zadd('doom:leaderboard:efficiency', {player: efficiency})

                        if log_msg:
                            socketio.emit('leaderboard:update', {'log_msg': log_msg})
                            socketio.emit('gamelog:update', {'log_msg': log_msg})

                        pipe.execute()
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
