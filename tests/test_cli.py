import pytest

from conftest import make_port
from led_driver_rs485 import cli


@pytest.fixture
def ports(monkeypatch):
    found = [make_port("/dev/ttyUSB0", "FT232R USB UART")]
    monkeypatch.setattr(cli, "scan_ports", lambda usb_only=True: found)
    return found


def test_list_prints_ports(ports, capsys):
    assert cli.main(["list"]) == 0
    assert capsys.readouterr().out == "0: /dev/ttyUSB0 - FT232R USB UART\n"


def test_list_without_ports(ports, capsys):
    ports.clear()
    assert cli.main(["list"]) == 0
    assert "No USB serial ports found" in capsys.readouterr().out


def test_countdown_opens_device_path(monkeypatch, fake_controller, capsys):
    monkeypatch.setattr(cli, "LEDController", fake_controller)
    monkeypatch.setattr("led_driver_rs485.countdown.time.monotonic", iter(range(0, 10_000, 1)).__next__)
    monkeypatch.setattr(cli, "play_alarm", lambda: pytest.fail("alarm should be skipped"))

    assert cli.main(["countdown", "-p", "/dev/ttyUSB3", "-s", "2", "--no-sound"]) == 0
    led = fake_controller.instances[0]
    assert (led.port, led.shown, led.closed) == ("/dev/ttyUSB3", [2, 1, 0], True)
    assert "Timer: 00s" in capsys.readouterr().out


def test_countdown_reports_open_errors(monkeypatch, capsys):
    def no_ports(index, baudrate):
        raise RuntimeError("No serial ports found")

    monkeypatch.setattr(cli.LEDController, "from_port_list", no_ports)
    assert cli.main(["countdown", "-p", "0"]) == 1
    assert "No serial ports found" in capsys.readouterr().err


@pytest.mark.parametrize("args", [["countdown", "-s", "100"], ["countdown", "-s", "x"], ["countdown", "-a", "300"], []])
def test_rejects_bad_arguments(args):
    with pytest.raises(SystemExit) as exit_info:
        cli.main(args)
    assert exit_info.value.code == 2
