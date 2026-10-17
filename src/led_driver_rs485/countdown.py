"""Countdown on the two-digit display."""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from .controller import DEFAULT_ADDRESS, LEDController

MIN_SECONDS = 1
MAX_SECONDS = 99  # two digits


def validate_seconds(seconds: int) -> None:
    if not MIN_SECONDS <= seconds <= MAX_SECONDS:
        raise ValueError(f"seconds must be between {MIN_SECONDS} and {MAX_SECONDS}, got {seconds}")


def run_countdown(
    controller: LEDController,
    seconds: int,
    *,
    address: int = DEFAULT_ADDRESS,
    on_tick: Optional[Callable[[int], None]] = None,
    stop_event: Optional[threading.Event] = None,
    interval: float = 1.0,
) -> bool:
    """Show ``seconds``, ``seconds - 1``, ... ``0``, one value per ``interval``.

    Ticks are scheduled against a monotonic clock, so time spent talking to
    the board does not add up as drift. Returns True once 0 is shown, or
    False as soon as ``stop_event`` is set.
    """
    validate_seconds(seconds)
    stop_event = stop_event or threading.Event()
    start = time.monotonic()
    for step, remaining in enumerate(range(seconds, -1, -1)):
        controller.display_number(address, remaining)
        if on_tick is not None:
            on_tick(remaining)
        next_tick = start + (step + 1) * interval
        if remaining and stop_event.wait(max(0.0, next_tick - time.monotonic())):
            return False
    return True
