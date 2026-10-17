"""Runs one countdown at a time in a background thread and tracks its state."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, replace
from typing import Callable, Optional

from ..controller import LEDController
from ..countdown import run_countdown, validate_seconds
from ..sound import play_alarm

logger = logging.getLogger(__name__)

IDLE, RUNNING, FINISHED, STOPPED, ERROR = "idle", "running", "finished", "stopped", "error"


class CountdownBusyError(RuntimeError):
    """A countdown was requested while another one is still running."""


@dataclass(frozen=True)
class CountdownState:
    status: str = IDLE
    port: Optional[str] = None
    seconds: Optional[int] = None
    remaining: Optional[int] = None
    error: Optional[str] = None


class CountdownService:
    """Thread-safe owner of the (single) running countdown."""

    def __init__(
        self,
        controller_factory: Callable[..., LEDController] = LEDController,
        alarm: Callable[[], object] = play_alarm,
        interval: float = 1.0,
    ):
        self._controller_factory = controller_factory
        self._alarm = alarm
        self._interval = interval
        self._lock = threading.Lock()
        self._state = CountdownState()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @property
    def state(self) -> CountdownState:
        with self._lock:
            return self._state

    def start(self, port: str, seconds: int, baudrate: int, play_sound: bool = True) -> CountdownState:
        validate_seconds(seconds)
        with self._lock:
            if self._state.status == RUNNING:
                raise CountdownBusyError("A countdown is already running")
            self._stop_event = threading.Event()
            self._state = CountdownState(RUNNING, port=port, seconds=seconds, remaining=seconds)
            self._thread = threading.Thread(
                target=self._run,
                args=(port, seconds, baudrate, play_sound, self._stop_event),
                name="countdown",
                daemon=True,
            )
            self._thread.start()
            return self._state

    def stop(self, timeout: float = 2.0) -> CountdownState:
        """Ask the running countdown to stop and give it ``timeout`` seconds to do so."""
        with self._lock:
            running = self._state.status == RUNNING
            self._stop_event.set()
            thread = self._thread
        if running and thread is not None:
            thread.join(timeout)
        return self.state

    def join(self, timeout: Optional[float] = None) -> None:
        """Wait for the background thread (including the alarm) to finish."""
        thread = self._thread
        if thread is not None:
            thread.join(timeout)

    def _run(self, port: str, seconds: int, baudrate: int, play_sound: bool, stop_event: threading.Event) -> None:
        try:
            with self._controller_factory(port, baudrate=baudrate) as led:
                finished = run_countdown(
                    led,
                    seconds,
                    on_tick=lambda remaining: self._update(remaining=remaining),
                    stop_event=stop_event,
                    interval=self._interval,
                )
        except Exception as exc:
            logger.exception("Countdown on %s failed", port)
            self._update(status=ERROR, error=str(exc) or type(exc).__name__)
            return
        self._update(status=FINISHED if finished else STOPPED)
        if finished and play_sound:
            self._alarm()

    def _update(self, **changes) -> None:
        with self._lock:
            self._state = replace(self._state, **changes)
