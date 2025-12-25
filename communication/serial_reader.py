"""
RS232/RS485 Serial Communication Handler for TY001 RFID Reader
"""
import asyncio
import serial_asyncio
from loguru import logger
from typing import Optional
from communication.rfid_base import RFIDReaderBase, RFIDTag


class SerialRFIDReader(RFIDReaderBase):
    """
    RS232/RS485 Serial RFID Reader implementation
    Handles serial communication with TY001 RFID reader
    """

    def __init__(
        self,
        reader_id: str,
        port: str,
        baudrate: int = 115200,
        bytesize: int = 8,
        parity: str = 'N',
        stopbits: int = 1,
        anti_bounce_time: float = 2.0  # seconds
    ):
        super().__init__(reader_id)
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.anti_bounce_time = anti_bounce_time
        
        self.reader = None
        self.writer = None
        self._last_read_tags = {}  # Tag EPC -> timestamp for anti-bounce
        self._reconnect_delay = 5  # seconds

    async def connect(self):
        """Connect to serial port"""
        try:
            # Map parity
            parity_map = {'N': serial_asyncio.serial.PARITY_NONE,
                         'E': serial_asyncio.serial.PARITY_EVEN,
                         'O': serial_asyncio.serial.PARITY_ODD}
            
            self.reader, self.writer = await serial_asyncio.open_serial_connection(
                url=self.port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=parity_map.get(self.parity, serial_asyncio.serial.PARITY_NONE),
                stopbits=self.stopbits
            )
            self.is_connected = True
            logger.info(f"Connected to RFID reader {self.reader_id} on {self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to {self.port}: {e}")
            self.is_connected = False
            raise

    async def disconnect(self):
        """Disconnect from serial port"""
        self._running = False
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.is_connected = False
        logger.info(f"Disconnected from RFID reader {self.reader_id}")

    async def start_reading(self):
        """Start continuous reading with auto-reconnect"""
        self._running = True
        while self._running:
            try:
                if not self.is_connected:
                    await self.connect()
                
                await self._read_loop()
            except Exception as e:
                logger.error(f"Error in reading loop: {e}")
                self.is_connected = False
                if self._running:
                    logger.info(f"Reconnecting in {self._reconnect_delay} seconds...")
                    await asyncio.sleep(self._reconnect_delay)

    async def stop_reading(self):
        """Stop continuous reading"""
        self._running = False
        await self.disconnect()

    async def _read_loop(self):
        """Main reading loop"""
        while self._running and self.is_connected:
            try:
                # Read until newline or specific delimiter
                data = await asyncio.wait_for(self.reader.readuntil(b'\r\n'), timeout=1.0)
                await self._process_data(data)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error reading data: {e}")
                raise

    async def _process_data(self, data: bytes):
        """Process received data and extract EPC tag"""
        try:
            # Decode the data
            message = data.decode('ascii').strip()
            
            # TY001 reader typically sends: EPC,RSSI,Antenna
            # Format varies by configuration, this is a common format
            parts = message.split(',')
            
            if len(parts) >= 1:
                epc = parts[0].strip()
                rssi = float(parts[1]) if len(parts) > 1 else None
                antenna = int(parts[2]) if len(parts) > 2 else None
                
                # Validate EPC format (typically hex string)
                if self._validate_epc(epc):
                    # Anti-bounce filtering
                    if self._should_process_tag(epc):
                        tag = RFIDTag(
                            epc=epc,
                            reader_id=self.reader_id,
                            antenna_port=antenna,
                            rssi=rssi
                        )
                        await self._notify_tag(tag)
                        logger.debug(f"Tag read: {epc}")
                    else:
                        logger.debug(f"Tag {epc} filtered by anti-bounce")
        except Exception as e:
            logger.error(f"Error processing data: {e}")

    def _validate_epc(self, epc: str) -> bool:
        """Validate EPC format (hex string)"""
        if not epc or len(epc) < 4:
            return False
        try:
            # Check if valid hex
            int(epc, 16)
            return True
        except ValueError:
            return False

    def _should_process_tag(self, epc: str) -> bool:
        """Check if tag should be processed based on anti-bounce time"""
        import time
        current_time = time.time()
        
        if epc in self._last_read_tags:
            last_read = self._last_read_tags[epc]
            if current_time - last_read < self.anti_bounce_time:
                return False
        
        self._last_read_tags[epc] = current_time
        return True
