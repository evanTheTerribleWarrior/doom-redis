import React, { useEffect, useState } from 'react';
import { Tabs, Tab, Box, Select, MenuItem, InputLabel, FormControl, Container } from '@mui/material';
import { Link, useLocation, Routes, Route, Navigate } from 'react-router-dom';
import Leaderboard from './Leaderboard';
import MapDominators from './MapDominators';
import PerformanceTracker from './PerformanceTracker';

function WADSelector({ selectedWAD, onChange, wadOptions }) {
    return (
      <FormControl
        sx={{
          mb: 4,
          minWidth: 300,
          maxWidth: 400,
          mx: 'auto',
          backgroundColor: 'rgba(30, 30, 30, 0.85)',
          border: '2px solid #ff4444',
          borderRadius: 2,
          p: 1
        }}
      >
        <InputLabel
          id="wad-select-label"
          sx={{ color: '#ff4444', fontWeight: 'bold', fontSize: '1rem' }}
        >
          Select WAD
        </InputLabel>
        <Select
          labelId="wad-select-label"
          value={selectedWAD}
          onChange={(e) => onChange(e.target.value)}
          sx={{
            color: '#ffaaaa',
            borderColor: '#ff4444',
            '.MuiSelect-icon': { color: '#ff4444' },
          }}
        >
          {wadOptions.map(({ id, name }) => (
            <MenuItem
              key={id}
              value={id}
              sx={{
                color: '#f0f0f0',
                backgroundColor: '#1a1a1a',
                '&:hover': { backgroundColor: '#331111' }
              }}
            >
              {name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    );
  }
  
function StatsTabs() {
  const location = useLocation();
  const [value, setValue] = useState(0);

  useEffect(() => {
    switch (location.pathname) {
      case '/stats':
      case '/stats/leaderboard':
        setValue(0);
        break;
      case '/stats/map-dominators':
        setValue(1);
        break;
      case '/stats/performance':
        setValue(2);
        break;
      default:
        setValue(0);
        break;
    }
  }, [location.pathname]);

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
      <Tabs
        value={value}
        textColor="inherit"
        indicatorColor="secondary"
        centered
      >
        <Tab label="Leaderboard" component={Link} to="/stats/leaderboard" />
        <Tab label="Map Dominators" component={Link} to="/stats/map-dominators" />
        <Tab label="Performance" component={Link} to="/stats/performance" />
      </Tabs>
    </Box>
  );
}

export default function GameStats() {
  const [selectedWad, setSelectedWad] = useState('');
  const [wadOptions, setWadOptions] = useState([]);

  useEffect(() => {
    fetch('http://localhost:5000/api/wads/wadnames')
      .then(res => res.json())
      .then(wads => {
        setWadOptions(wads);
        if (wads.length > 0) {
          setSelectedWad(wads[0].id);
        }
      });
  }, []);

  return (
    <Container maxWidth="lg" sx={{ borderRadius: 2, p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
        <WADSelector selectedWAD={selectedWad} onChange={setSelectedWad} wadOptions={wadOptions} />
      </Box>
      <StatsTabs />
      <Routes>
        <Route path="/" element={<Navigate to="/stats/leaderboard" replace />} />
        <Route path="/leaderboard" element={<Leaderboard selectedWAD={selectedWad} />} />
        <Route path="/map-dominators" element={<MapDominators selectedWAD={selectedWad} />} />
        <Route path="/performance" element={<PerformanceTracker selectedWAD={selectedWad}   />} />
      </Routes>
    </Container>
  );
}
