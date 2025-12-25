from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database.database import Base


class RaceMode(str, enum.Enum):
    MOTOCROSS = "motocross"
    ENDURO = "enduro"


class RaceType(str, enum.Enum):
    TIME_BASED = "time"
    LAP_BASED = "laps"


class Rider(Base):
    __tablename__ = "riders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    number = Column(Integer, nullable=False, unique=True)
    team = Column(String)
    category = Column(String, nullable=False)
    epc_rfid = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    laps = relationship("Lap", back_populates="rider")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    race_mode = Column(Enum(RaceMode), nullable=False)
    race_type = Column(Enum(RaceType), nullable=False)
    max_laps = Column(Integer)  # For lap-based races
    max_duration = Column(Integer)  # For time-based races (in seconds)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rfid_readings = relationship("RFIDReading", back_populates="event")
    laps = relationship("Lap", back_populates="event")
    results = relationship("Result", back_populates="event")


class RFIDReading(Base):
    __tablename__ = "rfid_readings"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    epc_tag = Column(String, nullable=False)
    reader_id = Column(String)  # Identifier of the RFID reader
    antenna_port = Column(Integer)  # Antenna port number
    rssi = Column(Float)  # Signal strength
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_valid = Column(Boolean, default=True)  # After anti-bounce filtering

    # Relationships
    event = relationship("Event", back_populates="rfid_readings")


class Lap(Base):
    __tablename__ = "laps"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    rider_id = Column(Integer, ForeignKey("riders.id"), nullable=False)
    lap_number = Column(Integer, nullable=False)
    lap_time = Column(Float)  # Lap time in seconds
    total_time = Column(Float)  # Total time from race start in seconds
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    event = relationship("Event", back_populates="laps")
    rider = relationship("Rider", back_populates="laps")


class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    rider_id = Column(Integer, ForeignKey("riders.id"), nullable=False)
    position = Column(Integer)
    total_laps = Column(Integer, default=0)
    total_time = Column(Float)  # Total time in seconds
    best_lap_time = Column(Float)  # Best lap time in seconds
    average_lap_time = Column(Float)  # Average lap time in seconds
    status = Column(String)  # finished, dnf, dns, disqualified
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    event = relationship("Event", back_populates="results")
    rider = relationship("Rider")
