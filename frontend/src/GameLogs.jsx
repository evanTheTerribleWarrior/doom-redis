import React, { useEffect, useState } from "react";
import { Box, Paper, Typography, Card, CardContent, Divider } from "@mui/material";
import io from "socket.io-client";

const socket = io("http://localhost:5000");

export default function MapDominators() {
  const [logs, setLogs] = useState([]);
  const [chats, setChats] = useState([]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const logsRes = await fetch('http://localhost:5000/api/load_logs');
        const logsData = await logsRes.json();
        setLogs(logsData.reverse());

        const chatsRes = await fetch('http://localhost:5000/api/load_chat');
        const chatsData = await chatsRes.json();
        setChats(chatsData.reverse());
      } catch (err) {
        console.error("Error fetching history:", err);
      }
    };

    fetchHistory();

    // Live updates
    socket.on("gamelog:update", (data) => {
      console.log(`Update arrived: ${JSON.stringify(data)}`);
      setLogs(prev => [data.log_msg, ...prev].slice(0, 100));
    });

    socket.on("chat:update", (data) => {
      console.log(`Message arrived: ${JSON.stringify(data)}`);
      setChats(prev => [data.chat_msg, ...prev].slice(0, 100));
    });

    return () => {
      socket.off("gamelog:update");
      socket.off("chat:update");
    };
  }, []);

  return (
    <Box sx={{ width: '100%', height: '100%', backgroundColor: '#121212', color: '#f0f0f0', padding: 2 }}>
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2, height: 'calc(100vh - 50px)', mt: 2 }}>
        <Paper variant="outlined" sx={{ p: 2, backgroundColor: '#1c1c1c', overflowY: 'auto' }}>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: '#ff4444' }}>Game Events</Typography>
          <Divider sx={{ mb: 2, backgroundColor: '#ff4444' }} />
          {logs.map((log, index) => (
            <Card
              key={index}
              variant="outlined"
              sx={{
                mb: 1,
                backgroundColor: '#2a2a2a',
                color: '#f0f0f0',
                '&:hover': { backgroundColor: '#333' },
                transition: 'background-color 0.3s',
              }}
            >
              <CardContent>
                <Typography variant="body2">{log}</Typography>
              </CardContent>
            </Card>
          ))}
        </Paper>

        <Paper variant="outlined" sx={{ p: 2, backgroundColor: '#1c1c1c', overflowY: 'auto' }}>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: '#ff4444' }}>Player Chat</Typography>
          <Divider sx={{ mb: 2, backgroundColor: '#ff4444' }} />
          {chats.map((msg, index) => (
            <Card
              key={index}
              variant="outlined"
              sx={{
                mb: 1,
                backgroundColor: '#2a2a2a',
                color: '#f0f0f0',
                '&:hover': { backgroundColor: '#333' },
                transition: 'background-color 0.3s',
              }}
            >
              <CardContent>
                <Typography variant="body2">{msg}</Typography>
              </CardContent>
            </Card>
          ))}
        </Paper>
      </Box>
    </Box>
  );
}
