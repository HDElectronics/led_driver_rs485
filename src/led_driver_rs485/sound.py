"""Alarm sound played when a countdown reaches zero."""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

ALARM_FILE = Path(__file__).parent / "assets" / "alarm-clock-90867.mp3"


def play_alarm(sound_file: Union[str, Path, None] = None) -> bool:
    """Play the alarm and block until it ends. Logs instead of raising on failure.

    Uses ``afplay`` on macOS and ``ffplay``/``mpg123`` elsewhere; falls back to
    the optional ``playsound`` package (e.g. on Windows).
    """
    path = str(sound_file or ALARM_FILE)
    try:
        command = _player_command(path)
        if command:
            subprocess.run(command, check=True, capture_output=True)
        else:
            from playsound import playsound

            playsound(path)
    except Exception as exc:
        logger.warning("Could not play alarm sound: %s", exc)
        return False
    return True


def _player_command(path: str) -> Optional[list[str]]:
    if sys.platform == "darwin":
        return ["afplay", path]
    if shutil.which("ffplay"):
        return ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]
    if shutil.which("mpg123"):
        return ["mpg123", "-q", path]
    return None
