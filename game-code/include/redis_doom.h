#ifndef REDIS_DOOM_H
#define REDIS_DOOM_H

#include <hiredis/hiredis.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include "doomdef.h"
#include "doomstat.h"
#include "hu_lib.h"

#ifdef __APPLE__
    #define secure_getenv getenv
#endif

extern char doom_wad_id[41];

extern redisContext *mainContext;

extern boolean redischatmode;
extern char redischatbuffer[128];
extern int redischatlen;
extern hu_textline_t w_redischatinput;

extern boolean redisNotificationMode;
extern char redisNotificationBuffer[128];
extern int redisNotificationLen;
extern hu_textline_t w_redisNotification;
extern volatile int redisNotificationCounter;


// Helper function to check the redis reply
void FreeRedisReply(redisReply *reply);

// Starts the redis connection
int InitRedis(redisContext **c);

// Closes the redis connection
void CloseRedis(redisContext **c);

// Add new player to Redis. We don't modify the name in the function
void AddPlayerToRedis(redisContext *c, const char *playerName);

// Check if player exists already in Redis
long long PlayerExistsInRedis(redisContext *c, const char* playerName);

void CheckPlayerPassword(redisContext *c, const char *playerName);

void AnnouncePlayer(redisContext *c, const char *playerName);

void CalculateWADHash(void);

void SendWADHashToRedis(redisContext *c, const char *iwad_filename);

void GetCurrentEpisodeMap(char* buffer, size_t size);
const char* GetMobjTypeName(int mobjType);
const char* GetWeaponName(int weaponEnum);
void AddShotFiredToStream(redisContext *c, const char *playerName, int weaponEnum);
void AddKillToStream(redisContext *c, const char *playerName, int weaponEnum, int targetEnum);
void AddPlayerDeathToStream(redisContext *c, const char *playerName, int killerEnum, int playerX, int playerY);
void AddChatEvent(redisContext *c, const char *playerName, const char *message);
void* PubSubListenerThread(void *arg);
void StartPubSubListener(const char* playerName);
void StopPubSubListener();

#endif