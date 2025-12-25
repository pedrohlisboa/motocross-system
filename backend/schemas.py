"""
Pydantic schemas for API request/response models
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RaceModeEnum(str, Enum):
    MOTOCROSS = "motocross"
    ENDURO = "enduro"


class RaceTypeEnum(str, Enum):
    TIME_BASED = "time"
    LAP_BASED = "laps"


# Rider schemas
class RiderBase(BaseModel):
    name: str
    number: int
    team: Optional[str] = None
    category: str
    epc_rfid: str


class RiderCreate(RiderBase):
    pass


class RiderUpdate(BaseModel):
    name: Optional[str] = None
    number: Optional[int] = None
    team: Optional[str] = None
    category: Optional[str] = None
    epc_rfid: Optional[str] = None


class RiderResponse(RiderBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Event schemas
class EventBase(BaseModel):
    name: str
    description: Optional[str] = None
    race_mode: RaceModeEnum
    race_type: RaceTypeEnum
    max_laps: Optional[int] = None
    max_duration: Optional[int] = None  # in seconds


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    race_mode: Optional[RaceModeEnum] = None
    race_type: Optional[RaceTypeEnum] = None
    max_laps: Optional[int] = None
    max_duration: Optional[int] = None


class EventResponse(EventBase):
    id: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# RFID Reading schemas
class RFIDReadingResponse(BaseModel):
    id: int
    event_id: int
    epc_tag: str
    reader_id: Optional[str] = None
    antenna_port: Optional[int] = None
    rssi: Optional[float] = None
    timestamp: datetime
    is_valid: bool

    class Config:
        from_attributes = True


# Lap schemas
class LapResponse(BaseModel):
    id: int
    event_id: int
    rider_id: int
    lap_number: int
    lap_time: Optional[float] = None
    total_time: Optional[float] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# Result schemas
class ResultResponse(BaseModel):
    id: int
    event_id: int
    rider_id: int
    position: Optional[int] = None
    total_laps: int
    total_time: Optional[float] = None
    best_lap_time: Optional[float] = None
    average_lap_time: Optional[float] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


# Leaderboard schemas
class LeaderboardEntry(BaseModel):
    position: int
    rider_number: int
    rider_name: str
    team: Optional[str] = None
    category: str
    total_laps: int
    total_time: Optional[float] = None
    best_lap_time: Optional[float] = None
    average_lap_time: Optional[float] = None
    status: str


class LeaderboardResponse(BaseModel):
    event_id: int
    event_name: str
    entries: List[LeaderboardEntry]


# RFID Reader Configuration
class ReaderConfig(BaseModel):
    reader_type: str = Field(..., description="serial, wiegand, or tcpip")
    reader_id: str
    
    # Serial configuration
    port: Optional[str] = None
    baudrate: Optional[int] = 115200
    
    # Wiegand configuration
    d0_pin: Optional[int] = None
    d1_pin: Optional[int] = None
    format_length: Optional[int] = 26
    
    # TCP/IP configuration
    host: Optional[str] = None
    tcp_port: Optional[int] = 6000
    
    # Common settings
    anti_bounce_time: Optional[float] = 2.0


# Export formats
class ExportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


class ExportRequest(BaseModel):
    event_id: int
    format: ExportFormat
