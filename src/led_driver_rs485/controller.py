"""Serial transport for the RS485 LED driver board."""

from __future__ import annotations

import logging
import time

import serial
import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo

from . import protocol

logger = logging.getLogger(__name__)

DEFAULT_ADDRESS = 0x01
DEFAULT_BAUDRATE = 9600
BAUDRATES = (9600, 19200, 38400, 57600, 115200)


def scan_ports(usb_only: bool = True) -> list[ListPortInfo]:
    """Available serial ports sorted by device name, optionally USB adapters only."""
    ports = sorted(serial.tools.list_ports.comports(), key=lambda p: p.device)
    if usb_only:
        ports = [p for p in ports if "usb" in f"{p.description} {p.hwid}".lower()]
    return ports


class LEDController:
    """One RS485 LED driver board behind a serial port.

    Use it as a context manager so the port is always released::

        with LEDController("/dev/ttyUSB0") as led:
            led.display_number(DEFAULT_ADDRESS, 42)
    """

    def __init__(
        self,
        port: str,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = 1.0,
        response_delay: float = 0.5,
    ):
        self.response_delay = response_delay
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout,
        )

    @classmethod
    def from_port_list(cls, port_index: int = 0, *, usb_only: bool = True, **kwargs) -> LEDController:
        """Open the ``port_index``-th port reported by :func:`scan_ports`."""
        ports = scan_ports(usb_only)
        if not ports:
            raise RuntimeError("No serial ports found")
        if not 0 <= port_index < len(ports):
            raise IndexError(f"Port index {port_index} out of range (0-{len(ports) - 1})")
        return cls(ports[port_index].device, **kwargs)

    @property
    def port(self) -> str:
        return self.ser.port

    def send_command(self, address: int, command: int, payload: bytes = b"") -> bytes:
        """Send one frame and return whatever the board answers within ``response_delay``."""
        frame = protocol.build_frame(address, command, payload)
        self.ser.reset_input_buffer()  # stale bytes would otherwise show up in this reply
        self.ser.write(frame)
        self.ser.flush()
        logger.debug("TX %s", frame.hex(" "))
        time.sleep(self.response_delay)
        response = self.ser.read_all()
        logger.debug("RX %s", response.hex(" ") if response else "(nothing)")
        return response

    def display_content(
        self,
        address: int,
        content: bytes,
        *,
        bytes_per_item: int = 1,
        flash: bool = False,
        save: bool = False,
    ) -> bytes:
        """Show raw item data (``bytes_per_item`` bytes per digit) on the display."""
        payload = protocol.display_payload(content, bytes_per_item, flash=flash, save=save)
        return self.send_command(address, protocol.CMD_DISPLAY, payload)

    def display_number(
        self, address: int, value: int, *, digits: int = 2, flash: bool = False, save: bool = False
    ) -> bytes:
        """Show a non-negative integer, one digit per item."""
        content = protocol.number_to_digits(value, digits)
        return self.display_content(address, content, flash=flash, save=save)

    def close(self) -> None:
        self.ser.close()

    def __enter__(self) -> LEDController:
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
