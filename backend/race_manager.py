"""
Race Logic Manager
Handles lap tracking, timing, and leaderboard generation
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.orm import Session
from database.models import Event, Rider, Lap, Result, RFIDReading, RaceType
from communication.rfid_base import RFIDTag


class RaceManager:
    """Manages race logic, lap tracking, and results calculation"""

    def __init__(self, db: Session):
        self.db = db
        self.active_events: Dict[int, Event] = {}  # event_id -> Event
        self._rider_last_lap: Dict[tuple, datetime] = {}  # (event_id, rider_id) -> last lap time

    def start_event(self, event_id: int):
        """Start an event"""
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ValueError(f"Event {event_id} not found")
        
        event.is_active = True
        event.start_time = datetime.utcnow()
        event.end_time = None
        self.db.commit()
        
        self.active_events[event_id] = event
        logger.info(f"Started event {event_id}: {event.name}")

    def stop_event(self, event_id: int):
        """Stop an event and finalize results"""
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ValueError(f"Event {event_id} not found")
        
        event.is_active = False
        event.end_time = datetime.utcnow()
        self.db.commit()
        
        # Calculate final results
        self.calculate_results(event_id)
        
        if event_id in self.active_events:
            del self.active_events[event_id]
        
        logger.info(f"Stopped event {event_id}: {event.name}")

    async def process_rfid_tag(self, tag: RFIDTag, event_id: int):
        """Process an RFID tag reading and update lap tracking"""
        # Find rider by EPC
        rider = self.db.query(Rider).filter(Rider.epc_rfid == tag.epc).first()
        if not rider:
            logger.warning(f"Unknown RFID tag: {tag.epc}")
            return
        
        # Get event
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event or not event.is_active:
            logger.warning(f"Event {event_id} not active")
            return
        
        # Store RFID reading
        reading = RFIDReading(
            event_id=event_id,
            epc_tag=tag.epc,
            reader_id=tag.reader_id,
            antenna_port=tag.antenna_port,
            rssi=tag.rssi,
            timestamp=tag.timestamp,
            is_valid=True
        )
        self.db.add(reading)
        
        # Calculate lap
        await self._process_lap(event, rider, tag.timestamp)
        
        self.db.commit()

    async def _process_lap(self, event: Event, rider: Rider, timestamp: datetime):
        """Process a lap for a rider"""
        # Get previous laps
        laps = self.db.query(Lap).filter(
            Lap.event_id == event.id,
            Lap.rider_id == rider.id
        ).order_by(Lap.lap_number).all()
        
        # Calculate lap number
        lap_number = len(laps) + 1
        
        # Calculate times
        if event.start_time:
            total_time = (timestamp - event.start_time).total_seconds()
        else:
            total_time = 0
        
        if laps:
            # Lap time is time since last lap
            last_lap = laps[-1]
            lap_time = (timestamp - last_lap.timestamp).total_seconds()
        else:
            # First lap - time from start
            lap_time = total_time
        
        # Check if race should accept this lap
        if not self._should_accept_lap(event, lap_number, total_time):
            logger.debug(f"Lap not accepted for rider {rider.number} in event {event.id}")
            return
        
        # Create lap record
        lap = Lap(
            event_id=event.id,
            rider_id=rider.id,
            lap_number=lap_number,
            lap_time=lap_time,
            total_time=total_time,
            timestamp=timestamp
        )
        self.db.add(lap)
        
        logger.info(f"Lap {lap_number} recorded for rider {rider.number}: {lap_time:.2f}s")
        
        # Update results
        self._update_result(event, rider)

    def _should_accept_lap(self, event: Event, lap_number: int, total_time: float) -> bool:
        """Check if a lap should be accepted based on race rules"""
        if event.race_type == RaceType.LAP_BASED:
            # Check max laps
            if event.max_laps and lap_number > event.max_laps:
                return False
        
        elif event.race_type == RaceType.TIME_BASED:
            # Check max duration
            if event.max_duration and total_time > event.max_duration:
                return False
        
        return True

    def _update_result(self, event: Event, rider: Rider):
        """Update or create result for a rider"""
        # Get all laps
        laps = self.db.query(Lap).filter(
            Lap.event_id == event.id,
            Lap.rider_id == rider.id
        ).all()
        
        if not laps:
            return
        
        # Calculate statistics
        total_laps = len(laps)
        total_time = max(lap.total_time for lap in laps) if laps else 0
        lap_times = [lap.lap_time for lap in laps if lap.lap_time]
        best_lap_time = min(lap_times) if lap_times else None
        average_lap_time = sum(lap_times) / len(lap_times) if lap_times else None
        
        # Get or create result
        result = self.db.query(Result).filter(
            Result.event_id == event.id,
            Result.rider_id == rider.id
        ).first()
        
        if not result:
            result = Result(
                event_id=event.id,
                rider_id=rider.id,
                status='racing'
            )
            self.db.add(result)
        
        # Update result
        result.total_laps = total_laps
        result.total_time = total_time
        result.best_lap_time = best_lap_time
        result.average_lap_time = average_lap_time
        result.updated_at = datetime.utcnow()

    def calculate_results(self, event_id: int):
        """Calculate final positions for an event"""
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            return
        
        # Get all results
        results = self.db.query(Result).filter(
            Result.event_id == event_id
        ).all()
        
        # Sort by laps (descending) then by total time (ascending)
        results.sort(key=lambda r: (-r.total_laps, r.total_time if r.total_time else float('inf')))
        
        # Assign positions
        for position, result in enumerate(results, start=1):
            result.position = position
            if result.status == 'racing':
                result.status = 'finished'
        
        self.db.commit()
        logger.info(f"Calculated results for event {event_id}")

    def get_leaderboard(self, event_id: int) -> List[Dict]:
        """Get current leaderboard for an event"""
        results = self.db.query(Result, Rider).join(
            Rider, Result.rider_id == Rider.id
        ).filter(
            Result.event_id == event_id
        ).order_by(
            Result.total_laps.desc(),
            Result.total_time
        ).all()
        
        leaderboard = []
        for position, (result, rider) in enumerate(results, start=1):
            leaderboard.append({
                'position': position,
                'rider_number': rider.number,
                'rider_name': rider.name,
                'team': rider.team,
                'category': rider.category,
                'total_laps': result.total_laps,
                'total_time': result.total_time,
                'best_lap_time': result.best_lap_time,
                'average_lap_time': result.average_lap_time,
                'status': result.status
            })
        
        return leaderboard
