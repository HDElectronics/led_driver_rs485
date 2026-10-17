import pytest

from conftest import make_port
from led_driver_rs485.web import app as app_module
from led_driver_rs485.web import create_app
from led_driver_rs485.web.service import CountdownService

PORT = "/dev/ttyUSB0"


@pytest.fixture
def alarms():
    return []


@pytest.fixture
def service(fake_controller, alarms):
    service = CountdownService(controller_factory=fake_controller, alarm=lambda: alarms.append(1), interval=0)
    yield service
    service.stop()
    service.join(2)


@pytest.fixture
def client(monkeypatch, service):
    monkeypatch.setattr(app_module, "scan_ports", lambda: [make_port(PORT, "FT232R USB UART")])
    return create_app(service).test_client()


def start(client, **overrides):
    body = {"port": PORT, "seconds": 3, "baudrate": 9600, **overrides}
    return client.post("/api/countdown", json=body)


def test_index_renders_controls(client):
    html = client.get("/").get_data(as_text=True)
    assert 'id="countdown-form"' in html
    assert '<option value="115200">' in html


def test_lists_ports(client):
    assert client.get("/api/ports").get_json() == {
        "ports": [{"device": PORT, "description": "FT232R USB UART"}]
    }


def test_runs_countdown_and_plays_alarm(client, service, fake_controller, alarms):
    response = start(client, baudrate=19200)
    assert response.status_code == 202
    assert response.get_json()["status"] == "running"

    service.join(2)
    led = fake_controller.instances[0]
    assert (led.port, led.baudrate, led.shown, led.closed) == (PORT, 19200, [3, 2, 1, 0], True)
    assert alarms == [1]
    assert client.get("/api/countdown").get_json() == {
        "status": "finished", "port": PORT, "seconds": 3, "remaining": 0, "error": None,
    }


def test_can_skip_alarm(client, service, alarms):
    start(client, play_sound=False)
    service.join(2)
    assert alarms == []


def test_rejects_second_countdown_and_stops_first(client, service):
    service._interval = 10
    assert start(client).status_code == 202

    busy = start(client)
    assert busy.status_code == 409
    assert "already running" in busy.get_json()["error"]

    stopped = client.post("/api/countdown/stop").get_json()
    assert stopped["status"] == "stopped"
    assert stopped["remaining"] == 3


def test_reports_serial_errors(client, service, monkeypatch):
    def broken_port(port, baudrate):
        raise OSError(f"could not open port {port}: Resource busy")

    service._controller_factory = broken_port
    start(client)
    service.join(2)
    state = client.get("/api/countdown").get_json()
    assert state["status"] == "error"
    assert "Resource busy" in state["error"]


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"port": "/dev/ttyUSB9"}, "isn't connected"),
        ({"port": ""}, "Choose a serial port"),
        ({"seconds": 0}, "Seconds must be"),
        ({"seconds": 100}, "Seconds must be"),
        ({"seconds": "10"}, "Seconds must be"),
        ({"seconds": True}, "Seconds must be"),
        ({"baudrate": 1234}, "Baud rate must be"),
        ({"play_sound": "yes"}, "play_sound"),
    ],
)
def test_validates_input(client, overrides, message):
    response = start(client, **overrides)
    assert response.status_code == 400
    assert message in response.get_json()["error"]


def test_rejects_non_json_body(client):
    response = client.post("/api/countdown", data="seconds=10")
    assert response.status_code == 400
    assert "JSON object" in response.get_json()["error"]


def test_api_errors_are_json(client):
    response = client.get("/api/nope")
    assert response.status_code == 404
    assert "error" in response.get_json()
