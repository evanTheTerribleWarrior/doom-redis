
#ifndef REDIS_DOOM_H
#define REDIS_DOOM_H

#include "hiredis.h"
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


// Redis non-event functions
void HandleExitSignal(int sig);
void FreeRedisReply(redisReply *reply);
int InitRedis(redisContext **c);
void CloseRedis(redisContext **c);
void AddPlayerToRedis(redisContext *c, const char *playerName);
long long PlayerExistsInRedis(redisContext *c, const char* playerName);
void CheckPlayerPassword(redisContext *c, const char *playerName);
void AnnouncePlayer(redisContext *c, const char *playerName);
void SendWADHashToRedis(redisContext *c, const char *iwad_filename);
void RefreshOnlineStatus(const char* playerName, int force);

// Helper functions
void CalculateWADHash(void);
void GetCurrentEpisodeMap(char* buffer, size_t size);
const char* GetMobjTypeName(int mobjType);
const char* GetWeaponName(int weaponEnum);
weapontype_t GetWeaponEnumFromName(const char* name);

// Events functions
void AddShotFiredToStream(redisContext *c, const char *playerName, int weaponEnum);
void AddKillToStream(redisContext *c, const char *playerName, int weaponEnum, int targetEnum, int playerX, int playerY);
void AddPlayerDeathToStream(redisContext *c, const char *playerName, int killerEnum, int playerX, int playerY);
void SendPlayerMovement(redisContext *c, const char* playerName, int weaponEnum, int posX, int posY);
void AddChatEvent(redisContext *c, const char *playerName, const char *message);

// Boost functions
void GetBoostDetails(const char *boost);
void GiveAmmoToPlayer(int amount);
void GiveArmorToPlayer(int amount);
void GiveWeaponToPlayer(const char *weaponName);
void GiveGodModeToPlayer(int duration);

// PubSub thread functions
void* PubSubListenerThread(void *arg);
void StartPubSubListener(const char* playerName);
void StopPubSubListener();

#endif