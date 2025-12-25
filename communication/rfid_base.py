"""
Base RFID Reader Interface
All RFID reader implementations should inherit from this base class
"""
from abc import ABC, abstractmethod
from typing import Callable, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio


@dataclass
class RFIDTag:
    """Represents an RFID tag reading"""
    epc: str  # Electronic Product Code
    reader_id: str
    antenna_port: Optional[int] = None
    rssi: Optional[float] = None  # Signal strength
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class RFIDReaderBase(ABC):
    """Base class for all RFID reader implementations"""

    def __init__(self, reader_id: str):
        self.reader_id = reader_id
        self.is_connected = False
        self.tag_callback: Optional[Callable[[RFIDTag], None]] = None
        self._running = False

    @abstractmethod
    async def connect(self):
        """Connect to the RFID reader"""
        pass

    @abstractmethod
    async def disconnect(self):
        """Disconnect from the RFID reader"""
        pass

    @abstractmethod
    async def start_reading(self):
        """Start continuous reading"""
        pass

    @abstractmethod
    async def stop_reading(self):
        """Stop continuous reading"""
        pass

    def set_tag_callback(self, callback: Callable[[RFIDTag], None]):
        """Set callback function to be called when a tag is read"""
        self.tag_callback = callback

    async def _notify_tag(self, tag: RFIDTag):
        """Notify callback about a new tag reading"""
        if self.tag_callback:
            if asyncio.iscoroutinefunction(self.tag_callback):
                await self.tag_callback(tag)
            else:
                self.tag_callback(tag)
