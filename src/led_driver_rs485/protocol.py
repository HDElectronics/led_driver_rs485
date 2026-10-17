"""Wire protocol of the RS485 7-segment LED driver board.

Pure functions only (no I/O), so every byte that goes on the wire can be
unit-tested. A frame looks like this::

    0xFE | length | address | command | payload... | 0xFF | CRC (2 bytes, big-endian)

``length`` counts the bytes from the start byte through the end byte, i.e.
the whole frame except the CRC. The CRC is CRC-16/XMODEM over the same bytes.
"""

from __future__ import annotations

START_BYTE = 0xFE
END_BYTE = 0xFF

CMD_DISPLAY = 0x01

FLAG_FLASH = 0x80
FLAG_SAVE = 0x40

# The display command packs item count and bytes-per-item into one byte.
MAX_ITEMS = 0x0F
MAX_BYTES_PER_ITEM = 0x0F

_FRAME_OVERHEAD = 5  # start, length, address, command, end


def crc16(data: bytes) -> int:
    """CRC-16/XMODEM: polynomial 0x1021, initial value 0, no reflection."""
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = (crc << 1) ^ 0x1021 if crc & 0x8000 else crc << 1
            crc &= 0xFFFF
    return crc


def build_frame(address: int, command: int, payload: bytes = b"") -> bytes:
    """Wrap a command and its payload into a complete frame with CRC."""
    _check_byte("address", address)
    _check_byte("command", command)
    length = _FRAME_OVERHEAD + len(payload)
    if length > 0xFF:
        raise ValueError(f"payload too long: {len(payload)} bytes")
    frame = bytes([START_BYTE, length, address, command, *payload, END_BYTE])
    return frame + crc16(frame).to_bytes(2, "big")


def display_payload(
    content: bytes, bytes_per_item: int = 1, *, flash: bool = False, save: bool = False
) -> bytes:
    """Payload for CMD_DISPLAY: flags, format byte, then the raw item data.

    ``content`` holds ``bytes_per_item`` bytes per digit, first digit first.
    """
    if not 1 <= bytes_per_item <= MAX_BYTES_PER_ITEM:
        raise ValueError(f"bytes_per_item must be 1-{MAX_BYTES_PER_ITEM}, got {bytes_per_item}")
    items, remainder = divmod(len(content), bytes_per_item)
    if remainder:
        raise ValueError(
            f"content length {len(content)} is not a multiple of bytes_per_item={bytes_per_item}"
        )
    if not 1 <= items <= MAX_ITEMS:
        raise ValueError(f"display takes 1-{MAX_ITEMS} items, got {items}")
    flags = (FLAG_FLASH if flash else 0) | (FLAG_SAVE if save else 0)
    return bytes([flags, (items << 4) | bytes_per_item, *content])


def number_to_digits(value: int, digits: int) -> bytes:
    """Decimal digits of ``value``, least significant (rightmost) digit first."""
    if not 0 <= value < 10**digits:
        raise ValueError(f"{value} does not fit in {digits} digit(s)")
    return bytes((value // 10**i) % 10 for i in range(digits))


def _check_byte(name: str, value: int) -> None:
    if not 0 <= value <= 0xFF:
        raise ValueError(f"{name} must be 0-255, got {value}")
