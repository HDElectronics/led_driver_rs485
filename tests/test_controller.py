from unittest.mock import MagicMock

import pytest

from conftest import make_port
from led_driver_rs485 import controller as controller_module
from led_driver_rs485.controller import LEDController, scan_ports


@pytest.fixture
def serial_port(monkeypatch):
    port = MagicMock()
    port.read_all.return_value = b"\xAA"
    monkeypatch.setattr(controller_module.serial, "Serial", MagicMock(return_value=port))
    return port


@pytest.fixture
def led(serial_port):
    return LEDController("/dev/ttyUSB0", response_delay=0)


def test_send_command_writes_frame_and_returns_reply(led, serial_port):
    assert led.send_command(0x01, 0x01, bytes([0x00, 0x21, 2, 4])) == b"\xAA"
    serial_port.reset_input_buffer.assert_called_once()
    serial_port.write.assert_called_once_with(bytes.fromhex("fe0901010021 0204 ff 3e78"))


def test_display_number_sends_digits_least_significant_first(led, serial_port):
    led.display_number(0x01, 42)
    frame = serial_port.write.call_args.args[0]
    assert frame[4:8] == bytes([0x00, 0x21, 2, 4])


def test_display_number_rejects_values_that_do_not_fit(led, serial_port):
    with pytest.raises(ValueError):
        led.display_number(0x01, 120)
    serial_port.write.assert_not_called()


def test_context_manager_closes_port(led, serial_port):
    with led:
        pass
    serial_port.close.assert_called_once()


def test_scan_ports_filters_usb_and_sorts(monkeypatch):
    ports = [
        make_port("/dev/ttyUSB1"),
        make_port("/dev/ttyS0", description="ttyS0", hwid="PNP0501"),
        make_port("/dev/cu.usbserial-0001", description="FT232R", hwid="usb vid:pid=0403:6001"),
    ]
    monkeypatch.setattr(controller_module.serial.tools.list_ports, "comports", lambda: ports)

    assert [p.device for p in scan_ports()] == ["/dev/cu.usbserial-0001", "/dev/ttyUSB1"]
    assert len(scan_ports(usb_only=False)) == 3


def test_from_port_list_opens_selected_port(monkeypatch, serial_port):
    monkeypatch.setattr(
        controller_module, "scan_ports", lambda usb_only: [make_port("/dev/ttyUSB0"), make_port("/dev/ttyUSB1")]
    )
    led = LEDController.from_port_list(1, baudrate=19200)
    controller_module.serial.Serial.assert_called_once()
    assert controller_module.serial.Serial.call_args.kwargs["port"] == "/dev/ttyUSB1"
    assert controller_module.serial.Serial.call_args.kwargs["baudrate"] == 19200
    assert led.ser is serial_port


@pytest.mark.parametrize("ports, index, error", [([], 0, RuntimeError), ([1], 1, IndexError), ([1], -1, IndexError)])
def test_from_port_list_rejects_missing_ports(monkeypatch, ports, index, error):
    monkeypatch.setattr(controller_module, "scan_ports", lambda usb_only: [make_port("/dev/x")] * len(ports))
    with pytest.raises(error):
        LEDController.from_port_list(index)
