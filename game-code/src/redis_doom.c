#include "redis_doom.h"
#include "hu_stuff.h"
#include "w_checksum.h"

// Holds the generated hex ID for the WAD
char doom_wad_id[41];

redisContext *mainContext;

/* Redis Chat variables */
boolean redischatmode = false;
char redischatbuffer[128];
int redischatlen = 0;
hu_textline_t w_redischatinput;

/* Pub Sub Notifications variables */
boolean redisNotificationMode = false;
volatile int redisNotificationCounter;
boolean redisNotificationThreadRunning = false;
char redisNotificationBuffer[128];
int redisNotificationLen = 0;
hu_textline_t w_redisNotification;
redisContext *pubSubContext;
pthread_t pubSubThread;

// Helper function to print and free the reply object as needed
void FreeRedisReply(redisReply *reply) {
    if (!reply) {
        printf("[Redis Error]: NULL reply received.\n");
        return;
    }

    if (reply->type == REDIS_REPLY_ERROR) {
        printf("[Redis Error]: %s\n", reply->str);
    }

    freeReplyObject(reply);
}


// Initialise a Redis connection.
// Passing context by reference to use with global context
int InitRedis(redisContext **c)
{
    const char *host = getenv("REDIS_HOST");
    const char *port = getenv("REDIS_PORT");
    const char *password = getenv("REDIS_PASSWORD");

    if (!host) host = "127.0.0.1";
    if (!port) port = "6379";
    int port_int = atoi(port);

    *c = redisConnect(host, port_int);
    if (*c == NULL || (*c)->err) {
        if (*c) {
            printf("Redis connection error: %s\n", (*c)->errstr);
            redisFree(*c);
        } else {
            printf("Can't allocate redis context\n");
        }
        return -1;
    }

    if (password && strlen(password) > 0) {
        redisReply *reply = redisCommand(*c, "AUTH %s", password);
        if (reply == NULL) {
            printf("Redis AUTH failed\n");
            redisFree(*c);
            return -1;
        }
        freeReplyObject(reply);
    }

    printf("Connected to Redis at %s:%d\n", host, port_int);
    return 0;
}

// Close Redis connection
// Passing context by reference to use with global context
void CloseRedis(redisContext **c)
{
    if (*c) {
        redisFree(*c);
        *c = NULL;
    }
    printf("[Redis]: Closed Redis Connection\n");
}

// Player should be unique per Redis DB
void AddPlayerToRedis(redisContext *c, const char *playerName)
{
    redisReply *reply;
    const char *password = getenv("PLAYER_PASSWORD");

    if (strlen(password) == 0) {
        printf("[Redis Error] No password set for new player '%s'. Set PLAYER_PASSWORD in .env\n", playerName);
        exit(1);
    }

    // Add player hash with the password
    reply = redisCommand(c, "HSET doom:player-auth:%s password %s", playerName, password);
    FreeRedisReply(reply);
    
    // Add new player name in the set
    reply = redisCommand(c,"SADD doom:players %s", playerName);
    FreeRedisReply(reply);

    // Add player suggestion for autocomplete functionality in Player Search
    reply = redisCommand(c,"FT.SUGADD doom:player-search %s 1", playerName);
    FreeRedisReply(reply);

     // Add player in Timeseries to track metrics like efficiency
    reply = redisCommand(c,"TS.CREATE doom:wads:stats:%s:timeseries:%s:efficiency LABELS player %s RETENTION 2678400000", doom_wad_id, playerName, playerName);
    FreeRedisReply(reply);
}

// A very simple way to ensure each player is unique by throwing error
// if you put a playerName with another password
// Obviously not a "serious" security measure but then again it's about playing Doom...
void CheckPlayerPassword(redisContext *c, const char *playerName)
{
    redisReply *reply;
    const char *password = getenv("PLAYER_PASSWORD");
    
    reply = redisCommand(c, "HGET doom:player-auth:%s password", playerName);
    if (reply && reply->type == REDIS_REPLY_STRING) {
        if (strcmp(reply->str, password) != 0) {
            printf("[Redis Error] Invalid password for player %s. Exiting...\n", playerName);
            exit(1);
        }
    }
}

// Sends the event that the user joined, which should be pushed in-game
// to players as a PubSub notification from the backend
void AnnouncePlayer(redisContext *c, const char *playerName)
{
    redisReply *reply;

    char message[100];
    snprintf(message, sizeof(message), "Player Joined: %s", playerName);

    reply = redisCommand(c, "XADD doom:events * type joined playerName %s",playerName);
    FreeRedisReply(reply);
}

long long PlayerExistsInRedis(redisContext *c, const char* playerName)
{
    redisReply *reply;

    // We check if player exists in the set
    reply = redisCommand(c, "SISMEMBER doom:players %s", playerName);

    printf("[Redis] Checking if player '%s' exists: %lld\n", playerName, reply->integer);

    // We return the integer response from the reply struct/object, as defined here:
    // https://github.com/redis/hiredis/blob/master/hiredis.h
    long long exists = reply->integer;
    FreeRedisReply(reply);

    return exists;
}

// Uses the Doom function W_Checksum that provides the sha1 digest
// for the WAD data. Then we calculate a hex ID to use to uniquely identify
// the WAD so that we don't rely on filenames only
void CalculateWADHash(void) 
{
    sha1_digest_t digest;
    W_Checksum(digest);

    for (int i = 0; i < 20; ++i) {
        sprintf(doom_wad_id + i * 2, "%02x", digest[i]);
    }
    doom_wad_id[40] = '\0';

    printf("[WAD Hash] WAD ID: %s\n", doom_wad_id);
}

void SendWADHashToRedis(redisContext *c, const char *iwad_filename) 
{
    redisReply* reply;

    reply = redisCommand(c, "HSETNX doom:wads:wad-names %s %s", doom_wad_id, iwad_filename);
    FreeRedisReply(reply);
}

void GetCurrentEpisodeMap(char* buffer, size_t size) 
{
    if (buffer == NULL || size == 0) return;
    snprintf(buffer, size, "E%dM%d", gameepisode, gamemap);
}

const char* GetMobjTypeName(int mobjType) 
{
    switch (mobjType) {
        case MT_POSSESSED:     return "Former Human";
        case MT_SHOTGUY:       return "Shotgun Guy";
        case MT_CHAINGUY:      return "Chaingunner";
        case MT_TROOP:         return "Imp";
        case MT_SERGEANT:      return "Demon";
        case MT_SHADOWS:       return "Spectre";
        case MT_HEAD:          return "Cacodemon";
        case MT_BRUISER:       return "Baron of Hell";
        case MT_KNIGHT:        return "Hell Knight";
        case MT_SKULL:         return "Lost Soul";
        case MT_SPIDER:        return "Spider Mastermind";
        case MT_BABY:          return "Arachnotron";
        case MT_CYBORG:        return "Cyberdemon";
        case MT_PAIN:          return "Pain Elemental";
        case MT_FATSO:         return "Mancubus";
        case MT_VILE:          return "Arch-Vile";
        case MT_UNDEAD:        return "Revenant";
        case MT_WOLFSS:        return "Wolfenstein SS";
        case MT_KEEN:          return "Commander Keen";
        default:               return "Unknown";
    }
}

const char* GetWeaponName(int weaponEnum) 
{

    const char* weaponName;

    switch (weaponEnum) {
        case wp_fist: weaponName = "fist"; break;
        case wp_pistol: weaponName = "pistol"; break;
        case wp_shotgun: weaponName = "shotgun"; break;
        case wp_chaingun: weaponName = "chaingun"; break;
        case wp_missile: weaponName = "rocket"; break;
        case wp_plasma: weaponName = "plasma"; break;
        case wp_bfg: weaponName = "bfg"; break;
        case wp_chainsaw: weaponName = "chainsaw"; break;
        case wp_supershotgun: weaponName = "supershotgun"; break;
        default: weaponName = "unknown"; break;
    }

    return weaponName;
}


void AddShotFiredToStream(redisContext *c, const char *playerName, int weaponEnum) 
{
    redisReply *reply;

    const char* weaponName = GetWeaponName(weaponEnum);
    char mapName[16];
    GetCurrentEpisodeMap(mapName, sizeof(mapName));

    reply = redisCommand(c, "XADD doom:events MAXLEN ~ 5000 * type shot playerName %s weaponName %s mapName %s wadId %s", playerName, weaponName, mapName, doom_wad_id);
    FreeRedisReply(reply);
}

void AddKillToStream(redisContext *c, const char *playerName, int weaponEnum, int targetEnum, int playerX, int playerY)
{

    redisReply *reply;

    
    const char* weaponName = GetWeaponName(weaponEnum);
    char mapName[16];
    GetCurrentEpisodeMap(mapName, sizeof(mapName));
    const char* targetName = GetMobjTypeName(targetEnum);

    // Get only the integer part of the Doom map units
    int posX = playerX >> 16;
    int posY = playerY >> 16;

    reply = redisCommand(c, "XADD doom:events MAXLEN ~ 5000 * type kill playerName %s targetName %s weaponName %s mapName %s posX %d posY %d  wadId %s", playerName, targetName, weaponName, mapName, posX, posY, doom_wad_id);
    FreeRedisReply(reply);
}

void AddPlayerDeathToStream(redisContext *c, const char *playerName, int killerEnum, int playerX, int playerY)
{

    redisReply *reply;

    const char* killerName = GetMobjTypeName(killerEnum);
    char mapName[16];
    GetCurrentEpisodeMap(mapName, sizeof(mapName));

    // Get only the integer part of the Doom map units
    int deathX = playerX >> 16;
    int deathY = playerY >> 16;

    reply = redisCommand(c, "XADD doom:events MAXLEN ~ 5000 * type death playerName %s targetName %s mapName %s posX %d posY %d wadId %s", playerName, killerName, mapName, deathX, deathY, doom_wad_id);
    FreeRedisReply(reply);
}

void AddChatEvent(redisContext *c, const char *playerName, const char *message)
{
    redisReply *reply;

    reply = redisCommand(c, "XADD doom:chat MAXLEN ~ 100 * playerName %s message %s", playerName, message);
    FreeRedisReply(reply);
}

void SendPlayerMovement(redisContext *c, const char *playerName, int weaponEnum, int posX, int posY)
{
    redisReply *reply;

    const char* weaponName = GetWeaponName(weaponEnum);
    char mapName[16];
    GetCurrentEpisodeMap(mapName, sizeof(mapName));

    reply = redisCommand(c, "XADD doom:events MAXLEN ~ 5000 * type movement playerName %s weaponName %s mapName %s posX %d posY %d  wadId %s", playerName, weaponName, mapName, posX, posY, doom_wad_id);
    FreeRedisReply(reply);
}

/* 
*
*   Functions for Pub/Sub model for in-game notifications
*
 */

void SetPubSubMessage(const char* incomingMessage) 
{
    memset(redisNotificationBuffer, 0, sizeof(redisNotificationBuffer));
    strncpy(redisNotificationBuffer, incomingMessage, sizeof(redisNotificationBuffer));
    redisNotificationLen = strlen(redisNotificationBuffer);
    redisNotificationMode = true;
    DrawRedisNotification();
}

void* PubSubListenerThread(void *arg) 
{

    const char *playerName = (const char*) arg;
    redisReply *reply;

    if (InitRedis(&pubSubContext) == 0) {
        reply = redisCommand(pubSubContext, "SUBSCRIBE doom:player:%s", playerName);
        FreeRedisReply(reply);

        reply = redisCommand(pubSubContext, "SUBSCRIBE doom:players:broadcast");
        FreeRedisReply(reply);
    }
    else {
        printf("Could not subscribe to PubSub channel");
        return NULL;
    }

    redisNotificationThreadRunning = true;

    while (redisNotificationThreadRunning) {
        if (redisGetReply(pubSubContext, (void**)&reply) == REDIS_OK) {
            if (reply && reply->type == REDIS_REPLY_ARRAY && reply->elements == 3) {
                const char* incomingMessage = reply->element[2]->str;
                if (incomingMessage) {
                    SetPubSubMessage(incomingMessage);
                }
            }
            freeReplyObject(reply);
        }
    }

    redisFree(pubSubContext);
    return NULL;

}

void StartPubSubListener(const char* playerName) 
{
    pthread_create(&pubSubThread, NULL, PubSubListenerThread, (void*)playerName);
}

void StopPubSubListener() 
{
    redisNotificationThreadRunning = false;
    if (pubSubContext) {
        redisFree(pubSubContext);
        pubSubContext = NULL;
    }
    pthread_cancel(pubSubThread);
}

/* 
*
*   End of Functions for Pub/Sub model for in-game notifications
*
 */