from types import SimpleNamespace

import pytest


class FakeController:
    """Stands in for LEDController; records every value shown."""

    instances = []

    def __init__(self, port="/dev/ttyFAKE0", baudrate=9600, **_):
        self.port = port
        self.baudrate = baudrate
        self.shown = []
        self.closed = False
        FakeController.instances.append(self)

    def display_number(self, address, value, **_):
        self.shown.append(value)
        return b""

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()


@pytest.fixture
def fake_controller():
    FakeController.instances = []
    return FakeController


def make_port(device, description="USB Serial", hwid="USB VID:PID=0403:6001"):
    return SimpleNamespace(device=device, description=description, hwid=hwid)
