SDL_CFLAGS = -D_REENTRANT -D_THREAD_SAFE -I/usr/include/SDL2 -I/opt/homebrew/include/SDL2
SDL_LIBS =
INCLUDES=-I../include
CC=gcc
CFLAGS+= $(INCLUDES) $(SDL_CFLAGS)
CFLAGS+=-Wall -DFEATURE_SOUND
LIBS+=-lm -lSDL2 -lSDL2_mixer `sdl2-config --cflags --libs` -lhiredis
OBJDIR=build
OUTPUT=redis-doom
SRC_DOOM = i_main.o \
			dummy.o \
			am_map.o \
			doomdef.o  \
			doomstat.o  \
			dstrings.o  \
			d_event.o  \
			d_items.o  \
			d_iwad.o  \
			d_loop.o  \
			d_main.o  \
			d_mode.o  \
			d_net.o  \
			f_finale.o  \
			f_wipe.o  \
			g_game.o  \
			hu_lib.o  \
			hu_stuff.o  \
			info.o  \
			i_cdmus.o  \
			i_endoom.o  \
			i_joystick.o  \
			i_scale.o  \
			i_sound.o  \
			i_sdlmusic.o   \
			i_sdlsound.o \
			i_system.o  \
			i_timer.o  \
			i_input.o   \
			i_video.o   \
			mus2mid.o   \
			memio.o  \
			m_argv.o  \
			m_bbox.o  \
			m_cheat.o  \
			m_config.o  \
			m_controls.o  \
			m_fixed.o  \
			m_menu.o  \
			m_misc.o  \
			m_random.o  \
			p_ceilng.o  \
			p_doors.o  \
			p_enemy.o  \
			p_floor.o  \
			p_inter.o  \
			p_lights.o  \
			p_map.o  \
			p_maputl.o  \
			p_mobj.o  \
			p_plats.o  \
			p_pspr.o  \
			p_saveg.o  \
			p_setup.o  \
			p_sight.o  \
			p_spec.o  \
			p_switch.o  \
			p_telept.o  \
			p_tick.o  \
			p_user.o  \
			r_bsp.o  \
			r_data.o  \
			r_draw.o  \
			r_main.o  \
			r_plane.o  \
			r_segs.o  \
			r_sky.o  \
			r_things.o  \
			sha1.o  \
			sounds.o  \
			statdump.o  \
			st_lib.o   \
			st_stuff.o   \
			s_sound.o   \
			tables.o   \
			v_video.o   \
			wi_stuff.o   \
			w_checksum.o   \
			w_file.o   \
			w_main.o   \
			w_wad.o   \
			z_zone.o   \
			w_file_stdc.o  \
			redis_doom.o

OBJS += $(addprefix $(OBJDIR)/, $(SRC_DOOM))

all:	 $(OUTPUT)

clean:
	rm -rf $(OBJDIR)
	rm -f $(OUTPUT)
	rm -f $(OUTPUT).exe
	rm -f $(OUTPUT).gdb
	rm -f $(OUTPUT).map

$(OUTPUT):	$(OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS) $(OBJS) \
	-o $(OUTPUT) $(LIBS)

$(OBJS): | $(OBJDIR)

$(OBJDIR):
	mkdir -p $(OBJDIR)

$(OBJDIR)/%.o:	%.c

	$(CC) $(CFLAGS) -c $< -o $@


