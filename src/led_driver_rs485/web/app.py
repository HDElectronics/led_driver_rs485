"""Flask web UI and JSON API."""

from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from flask import Blueprint, Flask, current_app, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from ..controller import BAUDRATES, DEFAULT_BAUDRATE, scan_ports
from ..countdown import MAX_SECONDS, MIN_SECONDS
from .service import CountdownBusyError, CountdownService

bp = Blueprint("countdown", __name__)


def create_app(service: Optional[CountdownService] = None) -> Flask:
    app = Flask(__name__)
    app.extensions["countdown"] = service or CountdownService()
    app.register_blueprint(bp)
    return app


@bp.get("/")
def index():
    return render_template(
        "index.html",
        baudrates=BAUDRATES,
        default_baudrate=DEFAULT_BAUDRATE,
        min_seconds=MIN_SECONDS,
        max_seconds=MAX_SECONDS,
    )


@bp.get("/api/ports")
def list_ports():
    return jsonify(ports=[{"device": p.device, "description": p.description} for p in scan_ports()])


@bp.get("/api/countdown")
def countdown_state():
    return jsonify(asdict(_service().state))


@bp.post("/api/countdown")
def start_countdown():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error("Request body must be a JSON object.", 400)

    port = data.get("port")
    seconds = data.get("seconds")
    baudrate = data.get("baudrate", DEFAULT_BAUDRATE)
    play_sound = data.get("play_sound", True)

    if not isinstance(port, str) or not port:
        return _error("Choose a serial port.", 400)
    if port not in {p.device for p in scan_ports()}:
        return _error(f"{port} isn't connected. Refresh the port list and pick another.", 400)
    if not _is_int(seconds) or not MIN_SECONDS <= seconds <= MAX_SECONDS:
        return _error(f"Seconds must be a whole number from {MIN_SECONDS} to {MAX_SECONDS}.", 400)
    if not _is_int(baudrate) or baudrate not in BAUDRATES:
        return _error(f"Baud rate must be one of {', '.join(map(str, BAUDRATES))}.", 400)
    if not isinstance(play_sound, bool):
        return _error("play_sound must be true or false.", 400)

    try:
        state = _service().start(port, seconds, baudrate, play_sound)
    except CountdownBusyError as exc:
        return _error(f"{exc}. Stop it first.", 409)
    return jsonify(asdict(state)), 202


@bp.post("/api/countdown/stop")
def stop_countdown():
    return jsonify(asdict(_service().stop()))


@bp.app_errorhandler(HTTPException)
def handle_http_error(exc: HTTPException):
    if request.path.startswith("/api/"):
        return _error(exc.description, exc.code)
    return exc


def _service() -> CountdownService:
    return current_app.extensions["countdown"]


def _error(message: str, status: int):
    return jsonify(error=message), status


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)
