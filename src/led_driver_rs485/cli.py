"""Command-line interface: ``led-driver {list,countdown,serve}``."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional, Sequence

import serial

from .controller import DEFAULT_ADDRESS, DEFAULT_BAUDRATE, LEDController, scan_ports
from .countdown import MAX_SECONDS, MIN_SECONDS, run_countdown
from .sound import play_alarm


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    return args.handler(args)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="led-driver", description="RS485 LED display controller")
    parser.add_argument("-v", "--verbose", action="store_true", help="log every frame sent and received")
    commands = parser.add_subparsers(dest="command", required=True)

    list_cmd = commands.add_parser("list", help="list serial ports")
    list_cmd.add_argument("--all", action="store_true", help="include non-USB ports")
    list_cmd.set_defaults(handler=_cmd_list)

    countdown = commands.add_parser("countdown", help="run a countdown on the display")
    countdown.add_argument(
        "-p", "--port", default="0",
        help="device path (e.g. /dev/ttyUSB0) or index from 'led-driver list' (default: 0)",
    )
    countdown.add_argument(
        "-s", "--seconds", type=_seconds, default=10,
        help=f"seconds to count down, {MIN_SECONDS}-{MAX_SECONDS} (default: 10)",
    )
    countdown.add_argument(
        "-b", "--baudrate", type=int, default=DEFAULT_BAUDRATE,
        help=f"serial baud rate (default: {DEFAULT_BAUDRATE})",
    )
    countdown.add_argument(
        "-a", "--address", type=_address, default=DEFAULT_ADDRESS,
        help=f"board address, decimal or 0x-hex (default: {DEFAULT_ADDRESS:#04x})",
    )
    countdown.add_argument("--no-sound", action="store_true", help="don't play the alarm at zero")
    countdown.set_defaults(handler=_cmd_countdown)

    serve = commands.add_parser("serve", help="start the web UI")
    serve.add_argument(
        "--host", default="127.0.0.1",
        help="interface to listen on; use 0.0.0.0 to allow other machines (default: 127.0.0.1)",
    )
    serve.add_argument("--port", type=int, default=8080, help="HTTP port (default: 8080)")
    serve.add_argument("--debug", action="store_true", help="enable Flask debug mode (local use only)")
    serve.set_defaults(handler=_cmd_serve)

    return parser


def _seconds(value: str) -> int:
    try:
        seconds = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a whole number: {value!r}") from None
    if not MIN_SECONDS <= seconds <= MAX_SECONDS:
        raise argparse.ArgumentTypeError(f"must be between {MIN_SECONDS} and {MAX_SECONDS}")
    return seconds


def _address(value: str) -> int:
    try:
        address = int(value, 0)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a number: {value!r}") from None
    if not 0 <= address <= 0xFF:
        raise argparse.ArgumentTypeError("must be between 0 and 255 (0x00-0xFF)")
    return address


def _cmd_list(args: argparse.Namespace) -> int:
    ports = scan_ports(usb_only=not args.all)
    if not ports:
        print("No serial ports found." if args.all else "No USB serial ports found.")
        return 0
    for index, port in enumerate(ports):
        print(f"{index}: {port.device} - {port.description}")
    return 0


def _cmd_countdown(args: argparse.Namespace) -> int:
    try:
        with _open_controller(args.port, args.baudrate) as led:
            print(f"Connected to {led.port}")
            run_countdown(
                led,
                args.seconds,
                address=args.address,
                on_tick=lambda remaining: print(f"Timer: {remaining:02d}s", flush=True),
            )
    except (serial.SerialException, RuntimeError, IndexError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
        return 130
    if not args.no_sound:
        play_alarm()
    return 0


def _open_controller(port: str, baudrate: int) -> LEDController:
    if port.isdigit():
        return LEDController.from_port_list(int(port), baudrate=baudrate)
    return LEDController(port, baudrate=baudrate)


def _cmd_serve(args: argparse.Namespace) -> int:
    try:
        from .web import create_app
    except ModuleNotFoundError as exc:
        if exc.name != "flask":
            raise
        print("The web UI needs Flask: pip install 'led_driver_rs485[web]'", file=sys.stderr)
        return 1
    create_app().run(host=args.host, port=args.port, debug=args.debug)
    return 0
