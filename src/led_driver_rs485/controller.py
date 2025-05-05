import serial
import serial.tools.list_ports
import struct
import time
from playsound import playsound


class LEDController:
    def __init__(self, port, baudrate=57600, timeout=1):
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout
        )

    def crc16(self, data: bytes) -> bytes:
        """Calculate CRC16 according to the provided C function."""
        crc = 0
        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
                crc &= 0xFFFF
        return struct.pack('>H', crc)

    def build_command(self, address, command, payload=b''):
        """Build full packet with CRC."""
        packet = bytearray()
        packet.append(0xFE)
        length = 1 + 1 + 1 + 1 + len(payload) + 1  # addr + cmd + flags + format + data + end
        packet.append(length)
        packet.append(address)
        packet.append(command)
        packet.extend(payload)
        packet.append(0xFF)
        packet.extend(self.crc16(packet))
        return packet

    def send_command(self, address, command, payload=b''):
        """Send command to the device (includes 500ms delay)."""
        packet = self.build_command(address, command, payload)
        self.ser.write(packet)
        time.sleep(0.5)
        return self.ser.read_all()

    def display_content(self, address, flash=False, save=False,
                        items=1, bytes_per_item=1, content_bytes=b''):
        """Command 0x01: Display content on 7-segments.

        bytes_per_item: number of data bytes per digit (usually 1).
        items: number of digits to update.
        content_bytes: raw data, length must equal items * bytes_per_item.
        """
        flags = (0x80 if flash else 0x00) | (0x40 if save else 0x00)
        fmt = ((items & 0xF) << 4) | (bytes_per_item & 0xF)
        payload = bytes([flags, fmt]) + content_bytes
        return self.send_command(address, 0x01, payload)

    def countdown(self, address, start_seconds: int, play_sound=True):
        """Count down from start_seconds to 0, updating two 7-segment digits each second."""
        for t in range(start_seconds, -1, -1):
            tens = (t // 10) % 10
            units = t % 10
            # Send two digits, one byte each
            self.display_content(
                address=address,
                flash=False,
                save=False,
                items=2,
                bytes_per_item=1,
                content_bytes=bytes([units, tens])
            )
            print(f"Timer: {t:02d}s")
            # send_command already waits 0.5s, add 0.5s to complete 1s interval
            time.sleep(0.5)
            if t == 0 and play_sound:
                playsound("alarm-clock-90867.mp3")

    def close(self):
        self.ser.close()

    @staticmethod
    def scan_ports(usb_only=True):
        ports = list(serial.tools.list_ports.comports())
        if usb_only:
            ports = [p for p in ports if "USB" in p.description or "usb" in p.hwid.lower()]
        return ports

    @classmethod
    def from_port_list(cls, port_index=0, baudrate=57600, timeout=1, usb_only=True):
        ports = cls.scan_ports(usb_only)
        if not ports:
            raise RuntimeError("No serial ports found")
        if port_index >= len(ports):
            raise IndexError(f"Port index {port_index} out of range (0-{len(ports)-1})")
        return cls(port=ports[port_index].device, baudrate=baudrate, timeout=timeout)
