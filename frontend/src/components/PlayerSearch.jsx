import React, { useEffect, useState } from 'react';
import {
  Card, CardContent, Typography, Box, Avatar,
  CircularProgress, TextField, InputAdornment, Grid
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import { Tooltip } from '@mui/material';
import MilitaryTechIcon from '@mui/icons-material/MilitaryTech';
import WhatshotIcon from '@mui/icons-material/Whatshot';
import BoltIcon from '@mui/icons-material/Bolt';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import StarIcon from '@mui/icons-material/Star';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import DoomSlayerImg from '../assets/doomslayer.png';

const badgeIconMap = {
  kill_streak_0: <MilitaryTechIcon sx={{ color: '#ffcc00' }} />,
  kill_streak_1: <WhatshotIcon sx={{ color: '#ff5722' }} />,
  kill_streak_2: <BoltIcon sx={{ color: '#e91e63' }} />,
  kill_streak_3: <EmojiEventsIcon sx={{ color: '#9c27b0' }} />,
  kill_streak_4: <StarIcon sx={{ color: '#03a9f4' }} />,
  kill_streak_5: <AutoAwesomeIcon sx={{ color: '#00e676' }} />
};

export default function PlayerSearch() {
  const [query, setQuery] = useState('');
  const [playerList, setPlayerList] = useState([]);
  const [loading, setLoading] = useState(false);

  const getLevel = (efficiency) => {
    if (efficiency >= 0.9) return 'DOOM GOD';
    if (efficiency >= 0.75) return 'Legend';
    if (efficiency >= 0.5) return 'Pro';
    if (efficiency >= 0.25) return 'Rookie';
    return 'Novice';
  };

  const fetchPlayers = async (term = '') => {
    setLoading(true);
    const res = await fetch(`http://localhost:5000/api/search_players?q=${term}`);
    const names = await res.json();

    const stats = await Promise.all(
      names.map(async (name) => {
        const res = await fetch(`http://localhost:5000/api/player/${name}`);
        return res.ok ? res.json() : null;
      })
    );

    setPlayerList(stats.filter(Boolean));
    setLoading(false);
  };

  useEffect(() => {
    fetchPlayers(query);
  }, [query]);

  return (
    <Box sx={{ px: 2, mt: 4 }}>
      <Box sx={{ maxWidth: 500, mx: 'auto', mb: 3 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search players..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          sx={{
            backgroundColor: '#1a1a1a',
            input: { color: '#ff4444' },
            '& .MuiOutlinedInput-root': {
              '& fieldset': { borderColor: '#ff4444' },
              '&:hover fieldset': { borderColor: '#ff8888' },
              '&.Mui-focused fieldset': { borderColor: '#ff4444' },
            },
          }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ color: '#ff4444' }} />
              </InputAdornment>
            )
          }}
        />
      </Box>

      {loading ? (
        <Box display="flex" justifyContent="center" mt={5}><CircularProgress color="error" /></Box>
      ) : (
        <Grid container spacing={3} justifyContent="center">
          {playerList.map((stats, i) => {
            const { player, kills, deaths, shots, efficiency, preferredWeapon, online } = stats;
            const level = getLevel(efficiency);

            return (
              <Grid item key={i} xs={12} sm={6} md={4} lg={3}>
                <Card sx={{ backgroundColor: '#1a1a1a', borderRadius: 3, boxShadow: '0 0 15px #ff4444aa', p: 2, position: 'relative' }}>
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={2}>
                      <Avatar alt="Doom Slayer" src={DoomSlayerImg} sx={{ width: 80, height: 80, border: '2px solid #ff4444' }} />
                      <Box>
                        <Typography variant="h6" sx={{ color: '#ff4444', fontWeight: 'bold' }}>{player}</Typography>
                        <Typography variant="subtitle2" sx={{ color: '#cccccc' }}>Level: <span style={{ color: '#ff8888' }}>{level}</span></Typography>
                      </Box>
                    </Box>

                    <Box mt={2}>
                      <Typography variant="body2" sx={{ color: '#f0f0f0' }}>Kills: <b>{kills}</b></Typography>
                      <Typography variant="body2" sx={{ color: '#f0f0f0' }}>Deaths: <b>{deaths}</b></Typography>
                      <Typography variant="body2" sx={{ color: '#f0f0f0' }}>Shots: <b>{shots}</b></Typography>
                      <Typography variant="body2" sx={{ color: '#f0f0f0' }}>Efficiency: <b>{efficiency}</b></Typography>
                      <Typography variant="body2" sx={{ color: '#f0f0f0' }}>Preferred Weapon: <b>{preferredWeapon}</b></Typography>
                      {stats.achievements && stats.achievements.length > 0 && (
                        <Box mt={2}>
                          <Typography variant="body2" sx={{ color: '#f0f0f0', mb: 1 }}>Achievements:</Typography>
                          <Box display="flex" flexWrap="wrap" gap={1}>
                          {stats.achievements.map((badge, i) => (
                            <Tooltip title={badge.description} key={i}>
                              {badgeIconMap[badge.key] || <MilitaryTechIcon sx={{ color: '#999' }} />}
                            </Tooltip>
                          ))}
                          </Box>
                        </Box>
                      )}
                    </Box>
                    
                  </CardContent>
                  <Box
                    sx={{
                      position: 'absolute',
                      bottom: 8,
                      right: 8,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1
                    }}
                  >
                    <Box
                      sx={{
                        width: 10,
                        height: 10,
                        borderRadius: '50%',
                        backgroundColor: online ? '#44ff44' : '#888888'
                      }}
                    />
                    <Typography variant="caption" sx={{ color: online ? '#44ff44' : '#888888' }}>
                      {online ? 'Online' : 'Offline'}
                    </Typography>
                  </Box>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}
    </Box>
  );
}
