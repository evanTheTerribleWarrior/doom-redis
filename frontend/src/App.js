import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Container, Tabs, Tab } from '@mui/material';
import Leaderboard from './Leaderboard';
import MapDominators from './MapDominators';
import GameLogs from './GameLogs';
import './App.css';

function AppTabs() {
  const location = useLocation();
  const [value, setValue] = React.useState(0);

  React.useEffect(() => {
    switch (location.pathname) {
      case '/':
        setValue(0);
        break;
      case '/map-dominators':
        setValue(1);
        break;
      case '/game-logs':
        setValue(2);
        break;
      default:
        setValue(0);
        break;
    }
  }, [location.pathname]);

  return (
    <Tabs value={value} textColor="inherit" indicatorColor="secondary">
      <Tab label="Leaderboard" component={Link} to="/" />
      <Tab label="Map Dominators" component={Link} to="/map-dominators" />
      <Tab label="Chat & Logs" component={Link} to="/game-logs" />
    </Tabs>
  );
}


export default function App() {
  return (
    <Router>
      <div className="doom-background">
        <AppBar position="static" color="transparent" elevation={0} sx={{ borderBottom: '1px solid #444' }}>
          <Toolbar>
            <Typography variant="h6" sx={{ flexGrow: 1, color: '#ff5555' }}>
              DOOM (powered by Redis)
            </Typography>
            <AppTabs />
          </Toolbar>
        </AppBar>
        <Container maxWidth="lg" sx={{ mt: 4, borderRadius: 2, p: 3 }}>
          <Routes>
            <Route path="/" element={<Leaderboard />} />
            <Route path="/map-dominators" element={<MapDominators />} />
            <Route path="/game-logs" element={<GameLogs />} />
          </Routes>
        </Container>
      </div>
    </Router>
  );
}
