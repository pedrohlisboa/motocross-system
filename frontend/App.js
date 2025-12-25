// React Frontend Entry Point - Motocross RFID Competition Management

import React, { useState, useEffect } from 'react';
import {
  AppBar, Toolbar, Typography, Container, Box, Tabs, Tab,
  Card, CardContent, Grid, Button, TextField, Dialog, DialogTitle,
  DialogContent, DialogActions, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Chip, IconButton,
  Select, MenuItem, FormControl, InputLabel
} from '@mui/material';
import {
  Add as AddIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [currentTab, setCurrentTab] = useState(0);
  const [riders, setRiders] = useState([]);
  const [events, setEvents] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  
  // Dialog states
  const [riderDialog, setRiderDialog] = useState(false);
  const [eventDialog, setEventDialog] = useState(false);
  
  // Form states
  const [riderForm, setRiderForm] = useState({
    name: '', number: '', team: '', category: '', epc_rfid: ''
  });
  const [eventForm, setEventForm] = useState({
    name: '', description: '', race_mode: 'motocross', race_type: 'laps',
    max_laps: 10, max_duration: 3600
  });

  useEffect(() => {
    fetchRiders();
    fetchEvents();
  }, []);

  useEffect(() => {
    if (selectedEvent) {
      fetchLeaderboard(selectedEvent);
      // Poll leaderboard every 3 seconds for real-time updates
      const interval = setInterval(() => fetchLeaderboard(selectedEvent), 3000);
      return () => clearInterval(interval);
    }
  }, [selectedEvent]);

  // API Calls
  const fetchRiders = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/riders`);
      const data = await response.json();
      setRiders(data);
    } catch (error) {
      console.error('Error fetching riders:', error);
    }
  };

  const fetchEvents = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/events`);
      const data = await response.json();
      setEvents(data);
      if (data.length > 0 && !selectedEvent) {
        setSelectedEvent(data[0].id);
      }
    } catch (error) {
      console.error('Error fetching events:', error);
    }
  };

  const fetchLeaderboard = async (eventId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/leaderboard/${eventId}`);
      const data = await response.json();
      setLeaderboard(data.entries || []);
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
    }
  };

  const createRider = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/riders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...riderForm,
          number: parseInt(riderForm.number)
        })
      });
      if (response.ok) {
        setRiderDialog(false);
        setRiderForm({ name: '', number: '', team: '', category: '', epc_rfid: '' });
        fetchRiders();
      }
    } catch (error) {
      console.error('Error creating rider:', error);
    }
  };

  const createEvent = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...eventForm,
          max_laps: parseInt(eventForm.max_laps),
          max_duration: parseInt(eventForm.max_duration)
        })
      });
      if (response.ok) {
        setEventDialog(false);
        setEventForm({
          name: '', description: '', race_mode: 'motocross', race_type: 'laps',
          max_laps: 10, max_duration: 3600
        });
        fetchEvents();
      }
    } catch (error) {
      console.error('Error creating event:', error);
    }
  };

  const startEvent = async (eventId) => {
    try {
      await fetch(`${API_BASE_URL}/events/${eventId}/start`, { method: 'POST' });
      fetchEvents();
    } catch (error) {
      console.error('Error starting event:', error);
    }
  };

  const stopEvent = async (eventId) => {
    try {
      await fetch(`${API_BASE_URL}/events/${eventId}/stop`, { method: 'POST' });
      fetchEvents();
    } catch (error) {
      console.error('Error stopping event:', error);
    }
  };

  const exportResults = async (eventId, format) => {
    try {
      const response = await fetch(`${API_BASE_URL}/reports/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId, format: format })
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `event_${eventId}_results.${format === 'excel' ? 'xlsx' : format}`;
        a.click();
      }
    } catch (error) {
      console.error('Error exporting results:', error);
    }
  };

  const formatTime = (seconds) => {
    if (!seconds) return '-';
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(3);
    return `${mins}:${secs.padStart(6, '0')}`;
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            🏍️ Motocross RFID Competition Management
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Tabs value={currentTab} onChange={(e, v) => setCurrentTab(v)} sx={{ mb: 3 }}>
          <Tab label="Live Leaderboard" />
          <Tab label="Riders" />
          <Tab label="Events" />
        </Tabs>

        {/* Live Leaderboard Tab */}
        {currentTab === 0 && (
          <Box>
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Select Event</InputLabel>
                  <Select
                    value={selectedEvent || ''}
                    label="Select Event"
                    onChange={(e) => setSelectedEvent(e.target.value)}
                  >
                    {events.map((event) => (
                      <MenuItem key={event.id} value={event.id}>
                        {event.name} {event.is_active && <Chip label="LIVE" color="success" size="small" sx={{ ml: 1 }} />}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={() => selectedEvent && fetchLeaderboard(selectedEvent)}
                  sx={{ mr: 1 }}
                >
                  Refresh
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={() => selectedEvent && exportResults(selectedEvent, 'pdf')}
                >
                  Export PDF
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={() => selectedEvent && exportResults(selectedEvent, 'excel')}
                  sx={{ ml: 1 }}
                >
                  Export Excel
                </Button>
              </Grid>
            </Grid>

            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                    <TableCell><strong>Pos</strong></TableCell>
                    <TableCell><strong>Number</strong></TableCell>
                    <TableCell><strong>Rider</strong></TableCell>
                    <TableCell><strong>Team</strong></TableCell>
                    <TableCell><strong>Category</strong></TableCell>
                    <TableCell align="right"><strong>Laps</strong></TableCell>
                    <TableCell align="right"><strong>Total Time</strong></TableCell>
                    <TableCell align="right"><strong>Best Lap</strong></TableCell>
                    <TableCell align="right"><strong>Avg Lap</strong></TableCell>
                    <TableCell><strong>Status</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {leaderboard.map((entry) => (
                    <TableRow key={entry.position}>
                      <TableCell>
                        <Chip
                          label={entry.position}
                          color={entry.position === 1 ? 'warning' : entry.position === 2 ? 'default' : entry.position === 3 ? 'default' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{entry.rider_number}</TableCell>
                      <TableCell>{entry.rider_name}</TableCell>
                      <TableCell>{entry.team || '-'}</TableCell>
                      <TableCell>{entry.category}</TableCell>
                      <TableCell align="right">{entry.total_laps}</TableCell>
                      <TableCell align="right">{formatTime(entry.total_time)}</TableCell>
                      <TableCell align="right">{formatTime(entry.best_lap_time)}</TableCell>
                      <TableCell align="right">{formatTime(entry.average_lap_time)}</TableCell>
                      <TableCell>
                        <Chip
                          label={entry.status}
                          color={entry.status === 'finished' ? 'success' : 'primary'}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {/* Riders Tab */}
        {currentTab === 1 && (
          <Box>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setRiderDialog(true)}
              sx={{ mb: 2 }}
            >
              Add Rider
            </Button>

            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                    <TableCell><strong>Number</strong></TableCell>
                    <TableCell><strong>Name</strong></TableCell>
                    <TableCell><strong>Team</strong></TableCell>
                    <TableCell><strong>Category</strong></TableCell>
                    <TableCell><strong>RFID Tag</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {riders.map((rider) => (
                    <TableRow key={rider.id}>
                      <TableCell><Chip label={rider.number} color="primary" /></TableCell>
                      <TableCell>{rider.name}</TableCell>
                      <TableCell>{rider.team || '-'}</TableCell>
                      <TableCell>{rider.category}</TableCell>
                      <TableCell><code>{rider.epc_rfid}</code></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {/* Events Tab */}
        {currentTab === 2 && (
          <Box>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setEventDialog(true)}
              sx={{ mb: 2 }}
            >
              Create Event
            </Button>

            <Grid container spacing={2}>
              {events.map((event) => (
                <Grid item xs={12} md={6} key={event.id}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">
                        {event.name}
                        {event.is_active && <Chip label="LIVE" color="success" size="small" sx={{ ml: 1 }} />}
                      </Typography>
                      <Typography color="text.secondary" gutterBottom>
                        {event.description}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Mode:</strong> {event.race_mode} | <strong>Type:</strong> {event.race_type}
                      </Typography>
                      {event.race_type === 'laps' && (
                        <Typography variant="body2">
                          <strong>Max Laps:</strong> {event.max_laps}
                        </Typography>
                      )}
                      {event.race_type === 'time' && (
                        <Typography variant="body2">
                          <strong>Duration:</strong> {Math.floor(event.max_duration / 60)} minutes
                        </Typography>
                      )}
                      <Box sx={{ mt: 2 }}>
                        {!event.is_active ? (
                          <Button
                            variant="contained"
                            color="success"
                            startIcon={<PlayIcon />}
                            onClick={() => startEvent(event.id)}
                          >
                            Start Event
                          </Button>
                        ) : (
                          <Button
                            variant="contained"
                            color="error"
                            startIcon={<StopIcon />}
                            onClick={() => stopEvent(event.id)}
                          >
                            Stop Event
                          </Button>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}
      </Container>

      {/* Rider Dialog */}
      <Dialog open={riderDialog} onClose={() => setRiderDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Rider</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Name"
            value={riderForm.name}
            onChange={(e) => setRiderForm({ ...riderForm, name: e.target.value })}
            sx={{ mt: 2, mb: 2 }}
          />
          <TextField
            fullWidth
            label="Number"
            type="number"
            value={riderForm.number}
            onChange={(e) => setRiderForm({ ...riderForm, number: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="Team"
            value={riderForm.team}
            onChange={(e) => setRiderForm({ ...riderForm, team: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="Category"
            value={riderForm.category}
            onChange={(e) => setRiderForm({ ...riderForm, category: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="RFID Tag (EPC)"
            value={riderForm.epc_rfid}
            onChange={(e) => setRiderForm({ ...riderForm, epc_rfid: e.target.value })}
            sx={{ mb: 2 }}
            helperText="Enter the UHF RFID tag EPC code"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRiderDialog(false)}>Cancel</Button>
          <Button onClick={createRider} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>

      {/* Event Dialog */}
      <Dialog open={eventDialog} onClose={() => setEventDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Event</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Event Name"
            value={eventForm.name}
            onChange={(e) => setEventForm({ ...eventForm, name: e.target.value })}
            sx={{ mt: 2, mb: 2 }}
          />
          <TextField
            fullWidth
            label="Description"
            multiline
            rows={2}
            value={eventForm.description}
            onChange={(e) => setEventForm({ ...eventForm, description: e.target.value })}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Race Mode</InputLabel>
            <Select
              value={eventForm.race_mode}
              label="Race Mode"
              onChange={(e) => setEventForm({ ...eventForm, race_mode: e.target.value })}
            >
              <MenuItem value="motocross">Motocross</MenuItem>
              <MenuItem value="enduro">Enduro</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Race Type</InputLabel>
            <Select
              value={eventForm.race_type}
              label="Race Type"
              onChange={(e) => setEventForm({ ...eventForm, race_type: e.target.value })}
            >
              <MenuItem value="laps">Lap-based</MenuItem>
              <MenuItem value="time">Time-based</MenuItem>
            </Select>
          </FormControl>
          {eventForm.race_type === 'laps' && (
            <TextField
              fullWidth
              label="Max Laps"
              type="number"
              value={eventForm.max_laps}
              onChange={(e) => setEventForm({ ...eventForm, max_laps: e.target.value })}
              sx={{ mb: 2 }}
            />
          )}
          {eventForm.race_type === 'time' && (
            <TextField
              fullWidth
              label="Duration (seconds)"
              type="number"
              value={eventForm.max_duration}
              onChange={(e) => setEventForm({ ...eventForm, max_duration: e.target.value })}
              sx={{ mb: 2 }}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEventDialog(false)}>Cancel</Button>
          <Button onClick={createEvent} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default App;