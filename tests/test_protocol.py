import pytest

from led_driver_rs485 import protocol


def test_crc16_matches_xmodem_check_value():
    assert protocol.crc16(b"123456789") == 0x31C3


def test_crc16_of_empty_input_is_zero():
    assert protocol.crc16(b"") == 0


# Frames captured from the original driver, so the wire format stays unchanged.
@pytest.mark.parametrize(
    "payload, expected",
    [
        (bytes([0x00, 0x21, 2, 4]), "fe 09 01 01 00 21 02 04 ff 3e 78"),
        (bytes([0x00, 0x21, 7, 0]), "fe 09 01 01 00 21 07 00 ff 19 4c"),
        (bytes([0x00, 0x21, 0, 0]), "fe 09 01 01 00 21 00 00 ff 9c dc"),
        (bytes([0xC0, 0x21, 5, 6]), "fe 09 01 01 c0 21 05 06 ff ee 32"),
    ],
)
def test_build_frame_matches_known_frames(payload, expected):
    assert protocol.build_frame(0x01, protocol.CMD_DISPLAY, payload).hex(" ") == expected


def test_length_byte_counts_frame_without_crc():
    frame = protocol.build_frame(0x05, 0x02, b"\xAA\xBB\xCC")
    assert frame[1] == len(frame) - 2
    assert frame[-3] == protocol.END_BYTE


@pytest.mark.parametrize("address, command", [(256, 1), (-1, 1), (1, 256)])
def test_build_frame_rejects_values_outside_a_byte(address, command):
    with pytest.raises(ValueError):
        protocol.build_frame(address, command)


def test_build_frame_rejects_payload_that_overflows_length_byte():
    with pytest.raises(ValueError, match="too long"):
        protocol.build_frame(1, 1, bytes(251))


def test_display_payload_packs_flags_and_format():
    payload = protocol.display_payload(b"\x05\x06", flash=True, save=True)
    assert payload == bytes([0xC0, 0x21, 5, 6])


def test_display_payload_supports_multi_byte_items():
    assert protocol.display_payload(b"\x01\x02\x03\x04", bytes_per_item=2)[1] == 0x22


@pytest.mark.parametrize(
    "content, bytes_per_item",
    [
        (b"", 1),                # no items
        (bytes(16), 1),          # more items than the format nibble holds
        (b"\x01\x02\x03", 2),    # partial item
        (b"\x01", 0),
        (b"\x01", 16),
    ],
)
def test_display_payload_rejects_inconsistent_content(content, bytes_per_item):
    with pytest.raises(ValueError):
        protocol.display_payload(content, bytes_per_item)


def test_number_to_digits_is_least_significant_first():
    assert protocol.number_to_digits(42, 2) == bytes([2, 4])
    assert protocol.number_to_digits(7, 2) == bytes([7, 0])
    assert protocol.number_to_digits(305, 3) == bytes([5, 0, 3])


@pytest.mark.parametrize("value", [-1, 100])
def test_number_to_digits_rejects_values_that_do_not_fit(value):
    with pytest.raises(ValueError):
        protocol.number_to_digits(value, 2)
