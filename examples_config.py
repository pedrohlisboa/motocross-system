"""
RFID Reader Configuration Examples
Demonstrates how to configure different RFID reader types
"""

# Example configurations for TY001 RFID Reader

SERIAL_READER_CONFIG = {
    "reader_type": "serial",
    "reader_id": "finish_line_serial",
    "port": "/dev/ttyUSB0",  # Linux/Mac: /dev/ttyUSB0, Windows: COM3
    "baudrate": 115200,
    "bytesize": 8,
    "parity": "N",  # N=None, E=Even, O=Odd
    "stopbits": 1,
    "anti_bounce_time": 2.0
}

TCPIP_READER_CONFIG = {
    "reader_type": "tcpip",
    "reader_id": "finish_line_network",
    "host": "192.168.1.100",
    "tcp_port": 6000,
    "anti_bounce_time": 2.0,
    "reconnect_delay": 5
}

WIEGAND_READER_CONFIG = {
    "reader_type": "wiegand",
    "reader_id": "finish_line_wiegand",
    "d0_pin": 17,  # GPIO pin for D0 (Raspberry Pi BCM numbering)
    "d1_pin": 18,  # GPIO pin for D1
    "format_length": 26,  # 26 for Wiegand-26, 34 for Wiegand-34
    "bit_timeout": 0.05,  # 50ms timeout between bits
    "anti_bounce_time": 2.0
}

# Multiple readers configuration
MULTI_READER_CONFIG = [
    {
        "reader_type": "tcpip",
        "reader_id": "start_line",
        "host": "192.168.1.100",
        "tcp_port": 6000,
        "anti_bounce_time": 2.0
    },
    {
        "reader_type": "tcpip",
        "reader_id": "finish_line",
        "host": "192.168.1.101",
        "tcp_port": 6000,
        "anti_bounce_time": 2.0
    }
]

# Event configuration examples
MOTOCROSS_EVENT = {
    "name": "MX Championship Round 1",
    "description": "First round of the national championship",
    "race_mode": "motocross",
    "race_type": "laps",
    "max_laps": 15,
    "max_duration": None
}

ENDURO_EVENT = {
    "name": "Enduro 3 Hour Challenge",
    "description": "3-hour endurance race",
    "race_mode": "enduro",
    "race_type": "time",
    "max_laps": None,
    "max_duration": 10800  # 3 hours in seconds
}

# Rider registration examples
SAMPLE_RIDERS = [
    {
        "name": "John Doe",
        "number": 1,
        "team": "Factory Racing",
        "category": "Pro",
        "epc_rfid": "E200123456789012"
    },
    {
        "name": "Jane Smith",
        "number": 2,
        "team": "Team Enduro",
        "category": "Pro",
        "epc_rfid": "E200987654321098"
    },
    {
        "name": "Mike Johnson",
        "number": 3,
        "team": "Independent",
        "category": "Amateur",
        "epc_rfid": "E200555555555555"
    }
]
