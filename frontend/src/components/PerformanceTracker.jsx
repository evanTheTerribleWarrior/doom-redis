import React, { useEffect, useState } from 'react';
import { Box, Typography, Select, MenuItem, InputLabel, FormControl, Paper } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import io from "socket.io-client";

const socket = io("http://localhost:5000");

export default function PerformanceTracker({ selectedWAD }) {
  const [players, setPlayers] = useState([]);
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [efficiencyData, setEfficiencyData] = useState([]);

  useEffect(() => {
    fetch('http://localhost:5000/api/players')
      .then(res => res.json())
      .then(data => {
        setPlayers(data);
        if (data.length > 0) setSelectedPlayer(data[0]);
      });
  }, []);

  useEffect(() => {
    if (!selectedPlayer || !selectedWAD) return;
    fetch(`http://localhost:5000/api/player/${selectedPlayer}/efficiency_timeseries?wadId=${selectedWAD}`)
      .then(res => res.json())
      .then(setEfficiencyData);
  }, [selectedPlayer, selectedWAD]);

  useEffect(() => {
    socket.on('efficiency:update', (data) => {
      if (data.player === selectedPlayer && data.wadId === selectedWAD) {
        fetch(`http://localhost:5000/api/player/${selectedPlayer}/efficiency_timeseries?wadId=${selectedWAD}`)
          .then(res => res.json())
          .then(setEfficiencyData);
      }
    });

    return () => socket.off('efficiency:update');
  }, [selectedPlayer, selectedWAD]);

  return (
    <Paper sx={{ p: 3, backgroundColor: 'rgba(20, 20, 20, 0.9)', boxShadow: '0 0 15px #ff4444aa', borderRadius: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
        <FormControl sx={{ minWidth: 300 }}>
          <InputLabel id="player-select-label" sx={{ color: '#ff4444' }}>Select Player</InputLabel>
          <Select
            labelId="player-select-label"
            value={selectedPlayer}
            onChange={(e) => setSelectedPlayer(e.target.value)}
            sx={{ color: '#ffaaaa', borderColor: '#ff4444', backgroundColor: '#1a1a1a' }}
          >
            {players.map(p => (
              <MenuItem key={p} value={p}>{p}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <Typography variant="h6" sx={{ textAlign: 'center', color: '#ff4444', mb: 2 }}>
        Efficiency Over Time
      </Typography>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={efficiencyData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#444" />
          <XAxis dataKey="timestamp" stroke="#aaa" />
          <YAxis domain={[0, 1]} stroke="#aaa" />
          <Tooltip contentStyle={{ backgroundColor: '#333', borderColor: '#ff4444' }} />
          <Legend />
          <Line type="monotone" dataKey="efficiency" stroke="#ff4444" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </Paper>
  );
}
