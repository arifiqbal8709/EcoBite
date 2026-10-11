const express = require('express');
const app = express();
const path = require('path');

const PORT = 3000;

// Middleware to serve static files (CSS, Images, JS)
app.use(express.static(path.join(__dirname, '../frontend')));
app.use(express.json()); // Enable JSON parsing for form submissions

// Route for the Home Page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/user', 'index.html'));
});

// Database Import
const donations = require('../database/db');

// Route for the Donate Page
app.get('/donate', (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/donor', 'donate.html'));
});

// Route for the Find Food Page
app.get('/find-food', (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/ngos', 'find-food.html'));
});

// Route for the Delivery Page
app.get('/delivery', (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/delivery', 'delivery.html'));
});

// Route for the Login Page
app.get('/login', (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/user', 'login.html'));
});

// Route for the Admin Page
app.get('/admin', (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/admin', 'admin.html'));
});

// Route for the Signup Page
app.get('/signup', (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/user', 'signup.html'));
});

// API: Handle Donation Submission
app.post('/api/donate', (req, res) => {
    const donation = req.body;
    // Add metadata
    donation.id = Date.now();
    donation.status = 'Available';
    donation.timestamp = new Date().toLocaleString();

    donations.push(donation); // Save to memory
    console.log('New Donation Added:', donation);

    res.json({ message: 'Donation received successfully!', id: donation.id });
});

// API: Update Donation Status
app.post('/api/update-status', (req, res) => {
    const { id, status } = req.body;
    const donation = donations.find(d => d.id === parseInt(id));

    if (donation) {
        donation.status = status;
        res.json({ success: true, message: `Status updated to ${status}` });
    } else {
        res.status(404).json({ success: false, message: 'Donation not found' });
    }
});

// API: Get All Donations
app.get('/api/donations', (req, res) => {
    res.json(donations);
});

// Start the server
app.listen(PORT, () => {
    console.log(`\n--------------------------------------------`);
    console.log(`   ShareMeal Server is Live! 🚀`);
    console.log(`   Open your browser at: http://localhost:${PORT}`);
    console.log(`--------------------------------------------\n`);
});
