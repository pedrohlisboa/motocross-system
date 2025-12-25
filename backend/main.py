# FastAPI Application Entry Point

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict
import asyncio
from loguru import logger
import sys

from database.database import get_db, init_db
from database.models import Rider, Event, RFIDReading, Lap, Result
from backend.schemas import (
    RiderCreate, RiderUpdate, RiderResponse,
    EventCreate, EventUpdate, EventResponse,
    RFIDReadingResponse, LapResponse, ResultResponse,
    LeaderboardResponse, LeaderboardEntry,
    ReaderConfig, ExportFormat, ExportRequest
)
from backend.race_manager import RaceManager
from backend.report_generator import ReportGenerator
from communication.rfid_base import RFIDTag
from communication.serial_reader import SerialRFIDReader
from communication.wiegand_reader import WiegandDecoder
from communication.tcpip_reader import TCPIPRFIDReader

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("logs/motocross_{time}.log", rotation="500 MB", level="DEBUG")

# Initialize FastAPI app
app = FastAPI(
    title="Motocross RFID Competition Management System",
    description="Complete motocross and enduro competition management with RFID integration",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
rfid_readers = {}  # reader_id -> reader instance
websocket_clients = []  # Active WebSocket connections
race_managers = {}  # db_session_id -> RaceManager (one per request)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Motocross System...")
    init_db()
    logger.info("Database initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Motocross System...")
    # Stop all RFID readers
    for reader_id, reader in rfid_readers.items():
        await reader.stop_reading()


# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Motocross RFID Competition Management System!",
        "version": "1.0.0",
        "endpoints": {
            "riders": "/riders",
            "events": "/events",
            "rfid_readings": "/rfid-readings",
            "leaderboard": "/leaderboard/{event_id}",
            "reports": "/reports/export"
        }
    }


# ==================== Rider Endpoints ====================

@app.post("/riders", response_model=RiderResponse, status_code=201)
def create_rider(rider: RiderCreate, db: Session = Depends(get_db)):
    """Register a new rider"""
    # Check if number or RFID already exists
    existing = db.query(Rider).filter(
        (Rider.number == rider.number) | (Rider.epc_rfid == rider.epc_rfid)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Rider number or RFID already exists")
    
    db_rider = Rider(**rider.dict())
    db.add(db_rider)
    db.commit()
    db.refresh(db_rider)
    logger.info(f"Created rider: {db_rider.name} (#{db_rider.number})")
    return db_rider


@app.get("/riders", response_model=List[RiderResponse])
def list_riders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all riders"""
    riders = db.query(Rider).offset(skip).limit(limit).all()
    return riders


@app.get("/riders/{rider_id}", response_model=RiderResponse)
def get_rider(rider_id: int, db: Session = Depends(get_db)):
    """Get a specific rider"""
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found")
    return rider


@app.put("/riders/{rider_id}", response_model=RiderResponse)
def update_rider(rider_id: int, rider_update: RiderUpdate, db: Session = Depends(get_db)):
    """Update a rider"""
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found")
    
    update_data = rider_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rider, field, value)
    
    db.commit()
    db.refresh(rider)
    logger.info(f"Updated rider: {rider.name} (#{rider.number})")
    return rider


@app.delete("/riders/{rider_id}", status_code=204)
def delete_rider(rider_id: int, db: Session = Depends(get_db)):
    """Delete a rider"""
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found")
    
    db.delete(rider)
    db.commit()
    logger.info(f"Deleted rider: {rider.name} (#{rider.number})")


# ==================== Event Endpoints ====================

@app.post("/events", response_model=EventResponse, status_code=201)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """Create a new event"""
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    logger.info(f"Created event: {db_event.name}")
    return db_event


@app.get("/events", response_model=List[EventResponse])
def list_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all events"""
    events = db.query(Event).offset(skip).limit(limit).all()
    return events


@app.get("/events/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get a specific event"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@app.post("/events/{event_id}/start")
def start_event(event_id: int, db: Session = Depends(get_db)):
    """Start an event"""
    race_manager = RaceManager(db)
    try:
        race_manager.start_event(event_id)
        return {"message": f"Event {event_id} started"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/events/{event_id}/stop")
def stop_event(event_id: int, db: Session = Depends(get_db)):
    """Stop an event and calculate final results"""
    race_manager = RaceManager(db)
    try:
        race_manager.stop_event(event_id)
        return {"message": f"Event {event_id} stopped"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== RFID Reader Endpoints ====================

@app.post("/rfid/readers/start")
async def start_rfid_reader(config: ReaderConfig, db: Session = Depends(get_db)):
    """Start an RFID reader"""
    if config.reader_id in rfid_readers:
        raise HTTPException(status_code=400, detail="Reader already running")
    
    try:
        # Create appropriate reader based on type
        if config.reader_type == "serial":
            reader = SerialRFIDReader(
                reader_id=config.reader_id,
                port=config.port,
                baudrate=config.baudrate,
                anti_bounce_time=config.anti_bounce_time
            )
        elif config.reader_type == "wiegand":
            reader = WiegandDecoder(
                reader_id=config.reader_id,
                d0_pin=config.d0_pin,
                d1_pin=config.d1_pin,
                format_length=config.format_length,
                anti_bounce_time=config.anti_bounce_time
            )
        elif config.reader_type == "tcpip":
            reader = TCPIPRFIDReader(
                reader_id=config.reader_id,
                host=config.host,
                port=config.tcp_port,
                anti_bounce_time=config.anti_bounce_time
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid reader type")
        
        # Set callback for tag readings
        async def tag_callback(tag: RFIDTag):
            # Find active event
            active_event = db.query(Event).filter(Event.is_active.is_(True)).first()
            if active_event:
                race_manager = RaceManager(db)
                await race_manager.process_rfid_tag(tag, active_event.id)
                
                # Notify WebSocket clients
                await broadcast_tag_reading(tag, active_event.id)
        
        reader.set_tag_callback(tag_callback)
        
        # Start reader in background
        rfid_readers[config.reader_id] = reader
        asyncio.create_task(reader.start_reading())
        
        logger.info(f"Started RFID reader: {config.reader_id} ({config.reader_type})")
        return {"message": f"Reader {config.reader_id} started"}
    
    except Exception as e:
        logger.error(f"Failed to start reader: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rfid/readers/{reader_id}/stop")
async def stop_rfid_reader(reader_id: str):
    """Stop an RFID reader"""
    if reader_id not in rfid_readers:
        raise HTTPException(status_code=404, detail="Reader not found")
    
    reader = rfid_readers[reader_id]
    await reader.stop_reading()
    del rfid_readers[reader_id]
    
    logger.info(f"Stopped RFID reader: {reader_id}")
    return {"message": f"Reader {reader_id} stopped"}


@app.get("/rfid/readers")
def list_readers():
    """List active RFID readers"""
    return {
        "readers": [
            {
                "reader_id": reader_id,
                "is_connected": reader.is_connected,
                "is_running": reader._running
            }
            for reader_id, reader in rfid_readers.items()
        ]
    }


# ==================== RFID Reading Endpoints ====================

@app.get("/rfid-readings", response_model=List[RFIDReadingResponse])
def list_rfid_readings(
    event_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List RFID readings"""
    query = db.query(RFIDReading)
    
    if event_id:
        query = query.filter(RFIDReading.event_id == event_id)
    
    readings = query.order_by(RFIDReading.timestamp.desc()).offset(skip).limit(limit).all()
    return readings


# ==================== Lap Endpoints ====================

@app.get("/laps", response_model=List[LapResponse])
def list_laps(
    event_id: int = None,
    rider_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List laps"""
    query = db.query(Lap)
    
    if event_id:
        query = query.filter(Lap.event_id == event_id)
    if rider_id:
        query = query.filter(Lap.rider_id == rider_id)
    
    laps = query.order_by(Lap.timestamp.desc()).offset(skip).limit(limit).all()
    return laps


# ==================== Results and Leaderboard ====================

@app.get("/results", response_model=List[ResultResponse])
def list_results(event_id: int = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List results"""
    query = db.query(Result)
    
    if event_id:
        query = query.filter(Result.event_id == event_id)
    
    results = query.order_by(Result.position).offset(skip).limit(limit).all()
    return results


@app.get("/leaderboard/{event_id}")
def get_leaderboard(event_id: int, db: Session = Depends(get_db)):
    """Get current leaderboard for an event"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    race_manager = RaceManager(db)
    leaderboard = race_manager.get_leaderboard(event_id)
    
    return {
        "event_id": event_id,
        "event_name": event.name,
        "entries": leaderboard
    }


# ==================== Reports ====================

@app.post("/reports/export")
def export_report(request: ExportRequest, db: Session = Depends(get_db)):
    """Export event results to PDF, Excel, or CSV"""
    generator = ReportGenerator(db)
    
    try:
        if request.format == ExportFormat.PDF:
            buffer = generator.generate_pdf(request.event_id)
            media_type = "application/pdf"
            filename = f"event_{request.event_id}_results.pdf"
        elif request.format == ExportFormat.EXCEL:
            buffer = generator.generate_excel(request.event_id)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"event_{request.event_id}_results.xlsx"
        elif request.format == ExportFormat.CSV:
            buffer = generator.generate_csv(request.event_id)
            media_type = "text/csv"
            filename = f"event_{request.event_id}_results.csv"
        else:
            raise HTTPException(status_code=400, detail="Invalid export format")
        
        return StreamingResponse(
            buffer,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail="Export failed")


# ==================== WebSocket for Real-time Updates ====================

@app.websocket("/ws/live-updates")
async def websocket_live_updates(websocket: WebSocket):
    """WebSocket endpoint for real-time race updates"""
    await websocket.accept()
    websocket_clients.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)


async def broadcast_tag_reading(tag: RFIDTag, event_id: int):
    """Broadcast RFID tag reading to all WebSocket clients"""
    message = {
        "type": "tag_reading",
        "event_id": event_id,
        "epc": tag.epc,
        "reader_id": tag.reader_id,
        "timestamp": tag.timestamp.isoformat()
    }
    
    # Send to all connected clients
    for client in websocket_clients:
        try:
            await client.send_json(message)
        except:
            # Remove disconnected clients
            websocket_clients.remove(client)