import threading

import pytest

from led_driver_rs485.countdown import run_countdown


def test_counts_down_to_zero(fake_controller):
    led = fake_controller()
    ticks = []
    assert run_countdown(led, 3, interval=0, on_tick=ticks.append) is True
    assert led.shown == [3, 2, 1, 0]
    assert ticks == [3, 2, 1, 0]


def test_stops_when_stop_event_is_set(fake_controller):
    led = fake_controller()
    stop = threading.Event()

    def on_tick(remaining):
        if remaining == 5:
            threading.Timer(0.05, stop.set).start()

    assert run_countdown(led, 5, interval=10, on_tick=on_tick, stop_event=stop) is False
    assert led.shown == [5]


def test_ticks_are_scheduled_against_start_time(fake_controller, monkeypatch):
    """Time spent sending a frame must not push later ticks back."""
    clock = {"now": 100.0}
    monkeypatch.setattr("led_driver_rs485.countdown.time.monotonic", lambda: clock["now"])

    class SlowController(fake_controller):
        def display_number(self, address, value, **kwargs):
            clock["now"] += 0.5  # serial round trip
            return super().display_number(address, value, **kwargs)

    waits = []

    class RecordingEvent(threading.Event):
        def wait(self, timeout=None):
            waits.append(timeout)
            clock["now"] += timeout
            return False

    run_countdown(SlowController(), 3, stop_event=RecordingEvent())
    assert waits == [0.5, 0.5, 0.5]


@pytest.mark.parametrize("seconds", [0, 100, -5])
def test_rejects_seconds_the_display_cannot_show(fake_controller, seconds):
    with pytest.raises(ValueError):
        run_countdown(fake_controller(), seconds, interval=0)
