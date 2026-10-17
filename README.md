# LED Driver RS485

Python driver, command-line tool and web UI for a two-digit 7-segment LED
display driven over RS485 (through a USB–RS485 adapter).

## Installation

```bash
pip install -e ".[web]"     # driver + CLI + web UI
pip install -e ".[dev]"     # ...plus pytest, for development
```

The alarm uses `afplay` on macOS and `ffplay` or `mpg123` on Linux. On other
systems install the `sound` extra (`pip install -e ".[sound]"`).

## Command line

```bash
led-driver list                         # USB serial ports, numbered
led-driver list --all                   # every serial port
led-driver countdown -p 0 -s 10         # port by index from `list`
led-driver countdown -p /dev/ttyUSB0 -s 30 -b 9600 --no-sound
led-driver -v countdown -s 5            # log every frame sent and received
led-driver serve                        # web UI on http://127.0.0.1:8080
```

`python -m led_driver_rs485 ...` works the same without the console script.

`serve` listens on localhost only. To control the display from another machine
use `led-driver serve --host 0.0.0.0` — anyone on the network can then drive it.

## Web UI

Pick the serial port, set the seconds (1–99) and baud rate, then select
**Start countdown**. The on-screen display mirrors the physical one, and
**Stop** ends the countdown early. The page polls the server, so reloading it
or opening it in a second browser shows the countdown already in progress.

JSON API:

| Method | Path                   | Body / result                                           |
| ------ | ---------------------- | ------------------------------------------------------- |
| GET    | `/api/ports`           | `{"ports": [{"device", "description"}]}`                |
| GET    | `/api/countdown`       | `{"status", "port", "seconds", "remaining", "error"}`   |
| POST   | `/api/countdown`       | `{"port", "seconds", "baudrate"?, "play_sound"?}` → 202 |
| POST   | `/api/countdown/stop`  | current state                                           |

`status` is one of `idle`, `running`, `finished`, `stopped`, `error`. Errors
come back as `{"error": "..."}` with a 4xx status; starting a countdown while
one is running returns 409.

## Library

```python
from led_driver_rs485 import DEFAULT_ADDRESS, LEDController, run_countdown

with LEDController("/dev/ttyUSB0", baudrate=9600) as led:
    led.display_number(DEFAULT_ADDRESS, 42)
    led.display_content(DEFAULT_ADDRESS, bytes([2, 4]), flash=True)
    run_countdown(led, 10, on_tick=print)
```

## Protocol

Every frame is

```
0xFE | length | address | command | payload ... | 0xFF | CRC16 (big-endian)
```

- `length` — number of bytes from `0xFE` through `0xFF` (the frame without the CRC).
- CRC — CRC-16/XMODEM (poly `0x1021`, init `0x0000`) over the same bytes.

Command `0x01` (display) takes the payload `flags | format | data`:

- `flags` — `0x80` flash, `0x40` save.
- `format` — high nibble: number of digits; low nibble: bytes per digit.
- `data` — the digit values, rightmost digit first.

Showing `42` on board `0x01`: `FE 09 01 01 00 21 02 04 FF 3E 78`.

## Layout

```
src/led_driver_rs485/
├── protocol.py      frame building, CRC, payload encoding (no I/O)
├── controller.py    LEDController: serial port transport, port scanning
├── countdown.py     drift-free, stoppable countdown
├── sound.py         alarm playback
├── cli.py           `led-driver` command
├── web/             Flask app, countdown service, page, CSS, JS
└── assets/          alarm sound
tests/               pytest suite; runs without hardware
```

## Tests

```bash
pytest
```

The serial port is mocked throughout, and frames are checked byte-for-byte
against frames captured from the original driver.

## License

MIT
