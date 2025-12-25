# Motocross RFID Competition Management System

A complete motocross and enduro competition management application with UHF RFID integration for real-time lap tracking and leaderboard generation.

## 🏍️ Features

### Core Functionality
- **Rider Registration**: Manage riders with name, number, team, category, and RFID tag (EPC)
- **Event Management**: Create and manage motocross and enduro races (time-based or lap-based)
- **Real-time RFID Integration**: Support for multiple RFID reader interfaces
  - RS232/RS485 serial communication
  - Wiegand 26/34 protocol decoding
  - TCP/IP network communication (RJ45)
- **Live Lap Tracking**: Automatic lap detection, timing, and position calculation
- **Real-time Leaderboard**: Live standings with lap times and positions
- **Results Export**: Generate reports in PDF, Excel, and CSV formats
- **WebSocket Support**: Real-time updates for race monitoring

### Technical Features
- **Modular Architecture**: Separate modules for RFID communication, race logic, database, and UI
- **Multi-reader Support**: Connect multiple RFID readers simultaneously
- **Anti-bounce Filtering**: Configurable debounce time to prevent duplicate reads
- **Auto-reconnection**: Robust error handling with automatic reconnection logic
- **Comprehensive Logging**: Detailed logs for debugging and audit trails
- **REST API**: Full API for mobile app integration

## 🛠️ Hardware Support

### RFID Reader: TY001 UHF RFID Reader
Supported interfaces:
- **RS232/RS485**: Serial communication with configurable baud rate, parity, stop bits
- **Wiegand 26/34**: GPIO-based bit decoding with parity checking
- **TCP/IP**: Network communication via RJ45 Ethernet

### RFID Tags
- Passive UHF RFID tags with EPC encoding

## 📦 Project Structure

```
motocross-system/
├── backend/                    # FastAPI backend application
│   ├── main.py                # Main API server with all endpoints
│   ├── schemas.py             # Pydantic models for request/response
│   ├── race_manager.py        # Race logic and lap tracking
│   └── report_generator.py    # PDF/Excel/CSV export functionality
├── communication/             # RFID reader modules
│   ├── rfid_base.py          # Base interface for RFID readers
│   ├── serial_reader.py      # RS232/RS485 implementation
│   ├── wiegand_reader.py     # Wiegand 26/34 decoder
│   └── tcpip_reader.py       # TCP/IP network reader
├── database/                  # Database layer
│   ├── database.py           # SQLAlchemy configuration
│   └── models.py             # Database models (Rider, Event, Lap, etc.)
├── frontend/                  # React web interface
│   ├── src/
│   │   └── main.jsx          # React entry point
│   ├── App.js                # Main application component
│   ├── package.json          # Frontend dependencies
│   └── vite.config.js        # Vite build configuration
├── requirements.txt          # Python dependencies
├── .env.example             # Example environment configuration
└── README.md                # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+ (for frontend)
- PostgreSQL or SQLite (SQLite is default)

### Backend Setup

1. **Clone the repository**
```bash
git clone https://github.com/pedrohlisboa/motocross-system.git
cd motocross-system
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
# Database will be initialized automatically on first run
```

6. **Start the backend server**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Start development server**
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 📡 RFID Reader Configuration

### RS232/RS485 Serial Reader

```python
# Example: Start a serial RFID reader
POST /rfid/readers/start
{
  "reader_type": "serial",
  "reader_id": "reader1",
  "port": "/dev/ttyUSB0",
  "baudrate": 115200,
  "anti_bounce_time": 2.0
}
```

### TCP/IP Network Reader

```python
# Example: Start a TCP/IP RFID reader
POST /rfid/readers/start
{
  "reader_type": "tcpip",
  "reader_id": "reader2",
  "host": "192.168.1.100",
  "tcp_port": 6000,
  "anti_bounce_time": 2.0
}
```

### Wiegand Reader

```python
# Example: Start a Wiegand reader (requires GPIO)
POST /rfid/readers/start
{
  "reader_type": "wiegand",
  "reader_id": "reader3",
  "d0_pin": 17,
  "d1_pin": 18,
  "format_length": 26,
  "anti_bounce_time": 2.0
}
```

## 🔌 API Endpoints

### Riders
- `POST /riders` - Create new rider
- `GET /riders` - List all riders
- `GET /riders/{id}` - Get rider details
- `PUT /riders/{id}` - Update rider
- `DELETE /riders/{id}` - Delete rider

### Events
- `POST /events` - Create new event
- `GET /events` - List all events
- `GET /events/{id}` - Get event details
- `POST /events/{id}/start` - Start event
- `POST /events/{id}/stop` - Stop event and finalize results

### RFID Readers
- `POST /rfid/readers/start` - Start RFID reader
- `POST /rfid/readers/{id}/stop` - Stop RFID reader
- `GET /rfid/readers` - List active readers

### Race Data
- `GET /rfid-readings` - List RFID readings
- `GET /laps` - List laps
- `GET /results` - List results
- `GET /leaderboard/{event_id}` - Get live leaderboard

### Reports
- `POST /reports/export` - Export results (PDF/Excel/CSV)

### WebSocket
- `WS /ws/live-updates` - Real-time race updates

## 📊 Database Schema

### Main Tables
- **riders**: Rider information and RFID tags
- **events**: Race events configuration
- **rfid_readings**: Raw RFID tag readings
- **laps**: Calculated lap times
- **results**: Final race results and statistics

## 🎯 Usage Examples

### 1. Register Riders
```bash
curl -X POST http://localhost:8000/riders \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "number": 42,
    "team": "Team Racing",
    "category": "Pro",
    "epc_rfid": "E2001234567890123456"
  }'
```

### 2. Create Event
```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Championship Round 1",
    "description": "First round of the season",
    "race_mode": "motocross",
    "race_type": "laps",
    "max_laps": 15
  }'
```

### 3. Start Event
```bash
curl -X POST http://localhost:8000/events/1/start
```

### 4. Start RFID Reader
```bash
curl -X POST http://localhost:8000/rfid/readers/start \
  -H "Content-Type: application/json" \
  -d '{
    "reader_type": "tcpip",
    "reader_id": "finish_line",
    "host": "192.168.1.100",
    "tcp_port": 6000
  }'
```

### 5. View Live Leaderboard
```bash
curl http://localhost:8000/leaderboard/1
```

### 6. Export Results
```bash
curl -X POST http://localhost:8000/reports/export \
  -H "Content-Type: application/json" \
  -d '{"event_id": 1, "format": "pdf"}' \
  --output results.pdf
```

## 🔧 Configuration

### Environment Variables
See `.env.example` for all available configuration options:
- Database connection
- RFID reader settings
- API configuration
- Logging levels

### Anti-bounce Configuration
Configure the anti-bounce time (in seconds) to prevent duplicate tag readings:
```python
"anti_bounce_time": 2.0  # Minimum time between same tag reads
```

## 🧪 Testing

### Run Backend Tests
```bash
pytest tests/
```

### Manual Testing
1. Start the backend server
2. Use the API documentation at `/docs` to test endpoints
3. Start the frontend and test the UI

## 📝 Logging

Logs are stored in the `logs/` directory:
- Rotation: 500 MB per file
- Format: Timestamped with log levels
- Includes RFID readings, errors, and audit trails

## 🔒 Security Considerations

- Change default credentials in production
- Use HTTPS for API communication
- Implement authentication/authorization for production use
- Validate RFID tag data before processing
- Sanitize user inputs

## 🚧 Future Enhancements

- [ ] Mobile app (iOS/Android)
- [ ] Offline mode with synchronization
- [ ] Advanced statistics and analytics
- [ ] Multi-language support
- [ ] User authentication and roles
- [ ] Live video integration
- [ ] Automated race start/stop based on scheduled times
- [ ] SMS/Email notifications
- [ ] Cloud deployment support

## 📄 License

This project is open source and available under the MIT License.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Developed with ❤️ for the motocross community**