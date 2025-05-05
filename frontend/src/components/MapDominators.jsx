import React, { useEffect, useState } from 'react';
import {
  Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, Paper
} from '@mui/material';
import io from 'socket.io-client';

const socket = io('http://localhost:5000');

export default function MapDominators({ selectedWAD }) {
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchData = (wadId) => {
      fetch(`http://localhost:5000/api/map-leaderboard?wadId=${wadId}`)
        .then(res => res.json())
        .then(setData);
    };

    if (selectedWAD) {
      fetchData(selectedWAD);
    }

    socket.on('leaderboard:update', (event) => {
      const updatedWadId = event.wadId || selectedWAD;
      if (updatedWadId === selectedWAD) {
        fetchData(updatedWadId);
      }
    });

    return () => {
      socket.off('leaderboard:update');
    };
  }, [selectedWAD]);

  return (
    <TableContainer component={Paper} sx={{ backgroundColor: 'rgba(20, 20, 20, 0.8)', borderRadius: 2, boxShadow: '0 0 15px #ff4444aa', p: 2 }}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell sx={{ color: '#ff4444', fontWeight: 'bold', textTransform: 'uppercase', borderBottom: '2px solid #ff4444' }}>Map</TableCell>
            <TableCell sx={{ color: '#ff4444', fontWeight: 'bold', textTransform: 'uppercase', borderBottom: '2px solid #ff4444' }}>Top Player</TableCell>
            <TableCell sx={{ color: '#ff4444', fontWeight: 'bold', textTransform: 'uppercase', borderBottom: '2px solid #ff4444' }}>Kills</TableCell>
            <TableCell sx={{ color: '#ff4444', fontWeight: 'bold', textTransform: 'uppercase', borderBottom: '2px solid #ff4444' }}>Efficiency</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((row, i) => (
            <TableRow key={i} sx={{ '&:hover': { backgroundColor: 'rgba(255, 68, 68, 0.1)' } }}>
              <TableCell sx={{ color: '#f0f0f0' }}>{row.map}</TableCell>
              <TableCell sx={{ color: '#f0f0f0' }}>{row.topPlayer}</TableCell>
              <TableCell sx={{ color: '#f0f0f0' }}>{row.kills}</TableCell>
              <TableCell sx={{ color: '#f0f0f0' }}>{row.efficiency}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
