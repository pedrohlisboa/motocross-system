"""
TCP/IP Network Communication Handler for RFID Reader
Handles socket communication with TY001 RFID reader over TCP/IP
"""
import asyncio
from loguru import logger
from typing import Optional
from communication.rfid_base import RFIDReaderBase, RFIDTag


class TCPIPRFIDReader(RFIDReaderBase):
    """
    TCP/IP network RFID reader implementation
    Maintains TCP connection with TY001 reader via RJ45
    """

    def __init__(
        self,
        reader_id: str,
        host: str,
        port: int = 6000,
        anti_bounce_time: float = 2.0,
        reconnect_delay: int = 5
    ):
        super().__init__(reader_id)
        self.host = host
        self.port = port
        self.anti_bounce_time = anti_bounce_time
        self.reconnect_delay = reconnect_delay
        
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self._last_read_tags = {}

    async def connect(self):
        """Establish TCP connection to RFID reader"""
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port
            )
            self.is_connected = True
            logger.info(f"Connected to RFID reader {self.reader_id} at {self.host}:{self.port}")
            
            # Send initialization command if needed
            await self._send_init_command()
        except Exception as e:
            logger.error(f"Failed to connect to {self.host}:{self.port}: {e}")
            self.is_connected = False
            raise

    async def disconnect(self):
        """Close TCP connection"""
        self._running = False
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.is_connected = False
        logger.info(f"Disconnected from RFID reader {self.reader_id}")

    async def _send_init_command(self):
        """Send initialization command to reader if needed"""
        # TY001 may require specific commands to start reading
        # This is reader-specific and should be configured based on documentation
        pass

    async def start_reading(self):
        """Start continuous reading with auto-reconnect"""
        self._running = True
        while self._running:
            try:
                if not self.is_connected:
                    await self.connect()
                
                await self._read_loop()
            except Exception as e:
                logger.error(f"Error in TCP reading loop: {e}")
                self.is_connected = False
                if self._running:
                    logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
                    await asyncio.sleep(self.reconnect_delay)

    async def stop_reading(self):
        """Stop continuous reading"""
        self._running = False
        await self.disconnect()

    async def _read_loop(self):
        """Main TCP reading loop"""
        while self._running and self.is_connected:
            try:
                # Read data from TCP stream
                # TY001 typically sends line-delimited messages
                data = await asyncio.wait_for(
                    self.reader.readuntil(b'\r\n'),
                    timeout=1.0
                )
                await self._process_data(data)
            except asyncio.TimeoutError:
                # No data received, continue
                continue
            except asyncio.IncompleteReadError:
                logger.error("Connection closed by reader")
                raise
            except Exception as e:
                logger.error(f"Error reading TCP data: {e}")
                raise

    async def _process_data(self, data: bytes):
        """Process received TCP data and extract tag information"""
        try:
            # Decode message
            message = data.decode('ascii').strip()
            
            # Parse TY001 TCP protocol
            # Format may vary: "EPC,RSSI,Antenna,Timestamp" or similar
            parts = message.split(',')
            
            if len(parts) >= 1:
                epc = parts[0].strip()
                rssi = float(parts[1]) if len(parts) > 1 else None
                antenna = int(parts[2]) if len(parts) > 2 else None
                
                # Validate EPC
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
                        logger.debug(f"TCP tag read: {epc}")
                    else:
                        logger.debug(f"Tag {epc} filtered by anti-bounce")
        except Exception as e:
            logger.error(f"Error processing TCP data: {e}")

    def _validate_epc(self, epc: str) -> bool:
        """Validate EPC format"""
        if not epc or len(epc) < 4:
            return False
        try:
            # Check if valid hex string
            int(epc, 16)
            return True
        except ValueError:
            return False

    def _should_process_tag(self, epc: str) -> bool:
        """Anti-bounce filtering based on time"""
        import time
        current_time = time.time()
        
        if epc in self._last_read_tags:
            last_read = self._last_read_tags[epc]
            if current_time - last_read < self.anti_bounce_time:
                return False
        
        self._last_read_tags[epc] = current_time
        return True

    async def send_command(self, command: str):
        """Send command to RFID reader"""
        if not self.is_connected or not self.writer:
            raise RuntimeError("Not connected to reader")
        
        try:
            self.writer.write(command.encode('ascii') + b'\r\n')
            await self.writer.drain()
            logger.debug(f"Sent command: {command}")
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            raise
