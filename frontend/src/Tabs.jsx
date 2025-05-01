// src/Tabs.jsx
import React, { useState } from 'react';
import Leaderboard from './Leaderboard';

export default function Tabs() {
  const [tab, setTab] = useState('leaderboard');

  const tabs = [
    { key: 'leaderboard', label: 'Leaderboard' },
    // Future tabs can be added here, like:
    // { key: 'deathmap', label: 'Deathmap' },
    // { key: 'chat', label: 'In-Game Chat' },
  ];

  return (
    <div>
      <div className="flex gap-4 mb-4">
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            className={`px-4 py-2 rounded ${tab === key ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            onClick={() => setTab(key)}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'leaderboard' && <Leaderboard />}
    </div>
  );
}