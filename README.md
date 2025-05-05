# LED Driver RS485

A Python library for controlling LED displays via RS485 protocol.

## Installation

```bash
# Install the package in development mode
pip install -e .
```

## Project Structure

```
led_driver_rs485/
├── src/                    # Source code package
│   └── led_driver_rs485/   # Main package
│       ├── __init__.py     # Package initialization
│       └── controller.py   # LED controller implementation
├── tests/                  # Test directory
│   ├── README.md           # Test documentation
│   └── test_led_driver_rs485.py  # Unit tests
├── main.py                 # Main script for running the application
├── setup.py                # Package setup file
├── requirements.txt        # Project dependencies
└── README.md               # This file
```

## Usage

### List Available Ports

```bash
python main.py list
```

### Run a Countdown

```bash
python main.py countdown --port 0 --seconds 10 --baudrate 9600
```

Or with short options:

```bash
python main.py countdown -p 0 -s 10 -b 9600
```

## Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
