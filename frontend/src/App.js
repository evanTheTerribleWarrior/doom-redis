import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Container, Tabs, Tab } from '@mui/material';
import GameLogs from './components/GameLogs';
import PlayerSearch from './components/PlayerSearch';
import GameStats from './components/GameStats';
import './App.css';

function AppTabs() {
  const location = useLocation();
  const [value, setValue] = React.useState(0);

  React.useEffect(() => {
    switch (location.pathname) {
      case '/':
      case '/stats':
        setValue(0);
        break;
      case '/game-logs':
        setValue(1);
        break;
      case '/player-search':
        setValue(2);
        break;
      default:
        setValue(0);
        break;
    }
  }, [location.pathname]);

  return (
    <Tabs value={value} textColor="inherit" indicatorColor="secondary">
      <Tab label="Stats" component={Link} to="/stats" />
      <Tab label="Chat & Logs" component={Link} to="/game-logs" />
      <Tab label="Player Search" component={Link} to="/player-search" />
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
        <Container maxWidth="lg" sx={{ borderRadius: 2}}>
          <Routes>
            <Route path="/" element={<GameStats />} />
            <Route path="/stats" element={<GameStats />} />
            <Route path="/stats/*" element={<GameStats />} />
            <Route path="/game-logs" element={<GameLogs />} />
            <Route path="/player-search" element={<PlayerSearch />} />
          </Routes>
        </Container>
      </div>
    </Router>
  );
}
