// Basic Express server for Waste Management App
// Note: This requires Node.js and Express to be installed

const express = require('express');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../frontend')));

// Sample data
const wasteData = {
  totalCollected: 1250,
  recycled: 450,
  landfill: 800,
  collections: [
    { area: 'North Zone', day: 'Monday', time: '9:00 AM', status: 'completed' },
    { area: 'East Zone', day: 'Tuesday', time: '10:00 AM', status: 'pending' },
    { area: 'West Zone', day: 'Wednesday', time: '9:30 AM', status: 'pending' }
  ]
};

// API Routes
app.get('/api/stats', (req, res) => {
  res.json({
    totalCollected: wasteData.totalCollected,
    recycled: wasteData.recycled,
    landfill: wasteData.landfill
  });
});

app.get('/api/collections', (req, res) => {
  res.json(wasteData.collections);
});

// Serve frontend for any other route
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/index.html'));
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});