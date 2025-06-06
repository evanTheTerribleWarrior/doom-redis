//
// Copyright(C) 1993-1996 Id Software, Inc.
// Copyright(C) 2005-2014 Simon Howard
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//


#include <stdlib.h>
#include <ctype.h>
#include <math.h>
#include <string.h>
#include <fcntl.h>
#include <stdio.h>
#include <SDL2/SDL.h>

#include "config.h"
#include "deh_str.h"
#include "doomtype.h"
#include "doomkeys.h"
#include "i_joystick.h"
#include "i_system.h"
#include "i_swap.h"
#include "i_timer.h"
#include "i_video.h"
#include "i_scale.h"
#include "m_argv.h"
#include "m_config.h"
#include "m_misc.h"
#include "tables.h"
#include "v_video.h"
#include "w_wad.h"
#include "z_zone.h"

// Check if we are in chat mode
#include "redis_doom.h"

#define KEYQUEUE_SIZE 16

static unsigned short s_KeyQueue[KEYQUEUE_SIZE];
static unsigned int s_KeyQueueWriteIndex = 0;
static unsigned int s_KeyQueueReadIndex = 0;

int vanilla_keyboard_mapping = 1;

// Is the shift key currently down?

static int shiftdown = 0;
static unsigned int lastRawKey = 0;

// Lookup table for mapping ASCII characters to their equivalent when
// shift is pressed on an American layout keyboard:
static const char shiftxform[] =
{
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
    11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
    21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
    31, ' ', '!', '"', '#', '$', '%', '&',
    '"', // shift-'
    '(', ')', '*', '+',
    '<', // shift-,
    '_', // shift--
    '>', // shift-.
    '?', // shift-/
    ')', // shift-0
    '!', // shift-1
    '@', // shift-2
    '#', // shift-3
    '$', // shift-4
    '%', // shift-5
    '^', // shift-6
    '&', // shift-7
    '*', // shift-8
    '(', // shift-9
    ':',
    ':', // shift-;
    '<',
    '+', // shift-=
    '>', '?', '@',
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
    'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
    '[', // shift-[
    '!', // shift-backslash - OH MY GOD DOES WATCOM SUCK
    ']', // shift-]
    '"', '_',
    '\'', // shift-`
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
    'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
    '{', '|', '}', '~', 127
};


extern boolean redischatmode;

// Get the equivalent ASCII (Unicode?) character for a keypress.

static unsigned char GetTypedChar(unsigned char key)
{

    // Is shift held down?  If so, perform a translation.
    if (shiftdown > 0)
    {
        if (key >= 0 && key < arrlen(shiftxform))
        {
            key = shiftxform[key];
        }
        else
        {
            key = 0;
        }
    }

    return key;
}

static unsigned char toDoomKey(unsigned int key)
{
    // Always allow these keys even in chat mode:
    if (key == SDLK_ESCAPE)
        return KEY_ESCAPE;
    if (key == SDLK_RETURN)
        return KEY_ENTER;
    if (key == SDLK_BACKSPACE)
        return KEY_BACKSPACE;

    if (redischatmode)
    {
        // Return raw keycode and defer shift handling to GetTypedChar
        return GetTypedChar(key);
    }

    // Gameplay key mappings
    switch (key)
    {
        case SDLK_F1: return KEY_F1;
        case SDLK_F2: return KEY_F2;
        case SDLK_F3: return KEY_F3;
        case SDLK_LALT:
        case SDLK_RALT: return KEY_LALT;
        case SDLK_LEFT: return KEY_LEFTARROW;
        case SDLK_RIGHT: return KEY_RIGHTARROW;
        case SDLK_UP: return KEY_UPARROW;
        case SDLK_DOWN: return KEY_DOWNARROW;
        case SDLK_LCTRL:
        case SDLK_RCTRL: return KEY_FIRE;
        case SDLK_SPACE: return KEY_USE;
        case SDLK_LSHIFT:
        case SDLK_RSHIFT: return KEY_RSHIFT;
        case SDL_BUTTON_RIGHT:
        case SDL_BUTTON_LEFT: return KEY_FIRE;
        case SDL_BUTTON_MIDDLE: return KEY_USE;
        default: return tolower(key);
    }
}



static void queueKeyPress(int pressed, unsigned int keyCode)
{
  lastRawKey = keyCode;
  unsigned char key = toDoomKey(keyCode);
  unsigned short keyData = (pressed << 8) | key;

  s_KeyQueue[s_KeyQueueWriteIndex] = keyData;
  s_KeyQueueWriteIndex++;
  s_KeyQueueWriteIndex %= KEYQUEUE_SIZE;
}

static void SDL_PollEvents() 
{
  SDL_Event e;

  while (SDL_PollEvent(&e))
  {
    if (e.type == SDL_QUIT)
    {
      atexit(SDL_Quit);
      exit(1);
    }

    if (e.type == SDL_KEYDOWN) 
    {
      //printf("KeyPress:%d sym:%d\n", e.xkey.keycode, sym);
      queueKeyPress(1, e.key.keysym.sym);
    } 
    else if (e.type == SDL_KEYUP) 
    {
      //printf("KeyRelease:%d sym:%d\n", e.xkey.keycode, sym);
      queueKeyPress(0, e.key.keysym.sym);
    }
    else if(e.type == SDL_MOUSEBUTTONDOWN) 
    {
      //printf("SDL_MOUSE_PRESSED: %d\n", e.button.button);
      queueKeyPress(1, e.button.button);
    }
    else if(e.type == SDL_MOUSEBUTTONUP)
    {
      //printf("SDL_MOUSE_RELEASED: %d\n", e.button.button);
      queueKeyPress(0, e.button.button);
    }

  }

}

int GetKey(int* pressed, unsigned char* doomKey)
{
    SDL_PollEvents();
    
    uint8_t k_pressed = 0;

    if (s_KeyQueueReadIndex == s_KeyQueueWriteIndex)
    {
        k_pressed = 0;
    } 
    else
    {
        unsigned short keyData = s_KeyQueue[s_KeyQueueReadIndex];
        s_KeyQueueReadIndex++;
        s_KeyQueueReadIndex %= KEYQUEUE_SIZE;
        *pressed = keyData >> 8;
        *doomKey = keyData & 0xFF;

        k_pressed = 1;
    }

    return k_pressed;
}




static void UpdateShiftStatus(int pressed, unsigned char key)
{
    int change;

    if (pressed) {
        change = 1;
    } else {
        change = -1;
    }

    if (lastRawKey == SDLK_LSHIFT || lastRawKey == SDLK_RSHIFT) {
      shiftdown += change;
    }
}


void I_GetEvent(void)
{
    event_t event;
    int pressed;
    unsigned char key;
    
	while (GetKey(&pressed, &key))
    {
        UpdateShiftStatus(pressed, key);

        // process event
        if(pressed)
        {
            // data1 has the key pressed, data2 has the character
            // (shift-translated, etc)
            event.type = ev_keydown;
            event.data1 = key;
            event.data2 = GetTypedChar(key);

            if (event.data1 != 0)
            {
                D_PostEvent(&event);
            }
        }
        else
        {
            event.type = ev_keyup;
            event.data1 = key;

            // data2 is just initialized to zero for ev_keyup.
            // For ev_keydown it's the shifted Unicode character
            // that was typed, but if something wants to detect
            // key releases it should do so based on data1
            // (key ID), not the printable char.

            event.data2 = 0;

            if (event.data1 != 0)
            {
                D_PostEvent(&event);
            }
            break;
        }
    }

}

void I_InitInput(void)
{
    
}

