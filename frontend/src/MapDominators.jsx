import React, { useEffect, useState } from 'react';
import {
  Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, TableSortLabel, Paper
} from '@mui/material';
import io from 'socket.io-client';

const socket = io('http://localhost:5000');

let externalUpdateHandler = null;

socket.on('connect', () => {
  console.log('[WS] Connected');
});

socket.on('leaderboard:update', () => {
  if (externalUpdateHandler) externalUpdateHandler();
});

export default function MapDominators() {
  const [data, setData] = useState([]);
  const [orderBy, setOrderBy] = useState('kills');
  const [order, setOrder] = useState('desc');

  useEffect(() => {
    const fetchData = () => {
      fetch('http://localhost:5000/api/map-leaderboard')
        .then(res => res.json())
        .then(setData);
    };

    fetchData();
    externalUpdateHandler = fetchData;

    return () => {
      externalUpdateHandler = null;
    };
  }, []);

  const handleSort = (property) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const sortedData = [...data].sort((a, b) => {
    const valA = a[orderBy];
    const valB = b[orderBy];
    if (valA < valB) return order === 'asc' ? -1 : 1;
    if (valA > valB) return order === 'asc' ? 1 : -1;
    return 0;
  });

  return (
    <TableContainer component={Paper} sx={{ backgroundColor: 'rgba(20, 20, 20, 0.8)', borderRadius: 2, boxShadow: '0 0 15px #ff4444aa', p: 2 }}>
      <Table>
        <TableHead>
          <TableRow>
            {['map', 'topPlayer', 'kills', 'efficiency'].map((column) => (
              <TableCell
                key={column}
                sx={{ color: '#ff4444', fontWeight: 'bold', textTransform: 'uppercase', borderBottom: '2px solid #ff4444' }}
              >
                <TableSortLabel
                  active={orderBy === column}
                  direction={orderBy === column ? order : 'asc'}
                  onClick={() => handleSort(column)}
                  sx={{ color: '#ff4444', '&.Mui-active': { color: '#ff8888' } }}
                >
                  {column.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </TableSortLabel>
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {sortedData.map((row, i) => (
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
