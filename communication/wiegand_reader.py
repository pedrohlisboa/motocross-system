"""
Wiegand 26/34 Decoder for RFID Reader
Decodes Wiegand protocol data streams into tag codes
"""
import asyncio
from loguru import logger
from typing import Optional, List
from communication.rfid_base import RFIDReaderBase, RFIDTag
import time


class WiegandDecoder(RFIDReaderBase):
    """
    Wiegand 26/34 protocol decoder
    Reads D0 and D1 bit pulses and decodes into tag codes
    
    Note: Wiegand typically requires hardware GPIO access.
    This is a simplified implementation that would need GPIO library integration.
    """

    def __init__(
        self,
        reader_id: str,
        d0_pin: Optional[int] = None,
        d1_pin: Optional[int] = None,
        bit_timeout: float = 0.05,  # 50ms between bits
        format_length: int = 26,  # Wiegand-26 or Wiegand-34
        anti_bounce_time: float = 2.0
    ):
        super().__init__(reader_id)
        self.d0_pin = d0_pin
        self.d1_pin = d1_pin
        self.bit_timeout = bit_timeout
        self.format_length = format_length
        self.anti_bounce_time = anti_bounce_time
        
        self._bits: List[int] = []
        self._last_bit_time = 0
        self._last_read_tags = {}
        
        # GPIO would be initialized here (e.g., using RPi.GPIO or gpiod)
        # For cross-platform compatibility, this is left as a placeholder
        self._gpio_available = False

    async def connect(self):
        """Initialize GPIO pins for Wiegand reading"""
        try:
            # Placeholder for GPIO initialization
            # In a real implementation:
            # import RPi.GPIO as GPIO
            # GPIO.setmode(GPIO.BCM)
            # GPIO.setup(self.d0_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            # GPIO.setup(self.d1_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            # GPIO.add_event_detect(self.d0_pin, GPIO.FALLING, callback=self._on_d0)
            # GPIO.add_event_detect(self.d1_pin, GPIO.FALLING, callback=self._on_d1)
            
            self.is_connected = True
            logger.info(f"Wiegand decoder {self.reader_id} initialized (format: W{self.format_length})")
            logger.warning("Note: GPIO integration required for actual hardware")
        except Exception as e:
            logger.error(f"Failed to initialize Wiegand decoder: {e}")
            raise

    async def disconnect(self):
        """Cleanup GPIO"""
        self._running = False
        # Placeholder for GPIO cleanup
        # GPIO.cleanup([self.d0_pin, self.d1_pin])
        self.is_connected = False
        logger.info(f"Wiegand decoder {self.reader_id} disconnected")

    async def start_reading(self):
        """Start monitoring for Wiegand pulses"""
        self._running = True
        logger.info(f"Wiegand reader {self.reader_id} started")
        
        # In real implementation, GPIO interrupts handle bit collection
        # This loop checks for completed reads
        while self._running:
            await asyncio.sleep(0.1)
            await self._check_complete_read()

    async def stop_reading(self):
        """Stop reading"""
        self._running = False
        await self.disconnect()

    def _on_d0(self, channel):
        """GPIO callback for D0 (binary 0) pulse"""
        current_time = time.time()
        
        # Check if this is a new read sequence
        if current_time - self._last_bit_time > self.bit_timeout:
            self._bits = []
        
        self._bits.append(0)
        self._last_bit_time = current_time

    def _on_d1(self, channel):
        """GPIO callback for D1 (binary 1) pulse"""
        current_time = time.time()
        
        # Check if this is a new read sequence
        if current_time - self._last_bit_time > self.bit_timeout:
            self._bits = []
        
        self._bits.append(1)
        self._last_bit_time = current_time

    async def _check_complete_read(self):
        """Check if a complete Wiegand sequence has been received"""
        if not self._bits:
            return
        
        current_time = time.time()
        
        # Check if enough time has passed since last bit (read complete)
        if current_time - self._last_bit_time > self.bit_timeout:
            if len(self._bits) == self.format_length:
                await self._decode_and_notify()
            else:
                logger.warning(f"Invalid Wiegand sequence length: {len(self._bits)}, expected {self.format_length}")
            
            self._bits = []

    async def _decode_and_notify(self):
        """Decode Wiegand bits and notify callback"""
        try:
            if self.format_length == 26:
                card_number = self._decode_wiegand26(self._bits)
            elif self.format_length == 34:
                card_number = self._decode_wiegand34(self._bits)
            else:
                logger.error(f"Unsupported Wiegand format: {self.format_length}")
                return
            
            if card_number and self._should_process_tag(card_number):
                # Convert to hex EPC format for consistency
                epc = format(card_number, 'X').zfill(8)
                
                tag = RFIDTag(
                    epc=epc,
                    reader_id=self.reader_id
                )
                await self._notify_tag(tag)
                logger.debug(f"Wiegand tag decoded: {epc}")
        except Exception as e:
            logger.error(f"Error decoding Wiegand: {e}")

    def _decode_wiegand26(self, bits: List[int]) -> Optional[int]:
        """Decode Wiegand-26 format"""
        # W26: [P_even][Facility Code 8 bits][Card Number 16 bits][P_odd]
        
        # Verify parity
        even_parity = bits[0]
        odd_parity = bits[25]
        
        # Extract data bits (skip parity bits)
        data_bits = bits[1:25]
        
        # Verify even parity (first 12 data bits)
        if sum(data_bits[:12]) % 2 != even_parity:
            logger.warning("Wiegand-26 even parity check failed")
            return None
        
        # Verify odd parity (last 12 data bits)
        if sum(data_bits[12:]) % 2 != (1 - odd_parity):
            logger.warning("Wiegand-26 odd parity check failed")
            return None
        
        # Extract facility code and card number
        facility_code = int(''.join(map(str, data_bits[:8])), 2)
        card_number = int(''.join(map(str, data_bits[8:])), 2)
        
        # Combine into single number
        return (facility_code << 16) | card_number

    def _decode_wiegand34(self, bits: List[int]) -> Optional[int]:
        """Decode Wiegand-34 format"""
        # W34: [P_even][Card Number 32 bits][P_odd]
        
        even_parity = bits[0]
        odd_parity = bits[33]
        
        data_bits = bits[1:33]
        
        # Verify even parity
        if sum(data_bits[:16]) % 2 != even_parity:
            logger.warning("Wiegand-34 even parity check failed")
            return None
        
        # Verify odd parity
        if sum(data_bits[16:]) % 2 != (1 - odd_parity):
            logger.warning("Wiegand-34 odd parity check failed")
            return None
        
        # Convert to integer
        card_number = int(''.join(map(str, data_bits)), 2)
        return card_number

    def _should_process_tag(self, card_number: int) -> bool:
        """Anti-bounce filtering"""
        current_time = time.time()
        epc = str(card_number)
        
        if epc in self._last_read_tags:
            last_read = self._last_read_tags[epc]
            if current_time - last_read < self.anti_bounce_time:
                return False
        
        self._last_read_tags[epc] = current_time
        return True
