# LED Driver RS485

A Python library for controlling LED displays via RS485 protocol.

## Installation

```bash
# Install the package in development mode
pip install -e .

# Install all dependencies including web app
pip install -r requirements.txt
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
├── web_app/                # Web application
│   ├── app.py              # Flask application
│   ├── templates/          # HTML templates
│   └── static/             # Static files (CSS, JS)
├── main.py                 # CLI script for running the application
├── run_web_app.py          # Script to run the web application
├── setup.py                # Package setup file
├── requirements.txt        # Project dependencies
└── README.md               # This file
```

## Usage

### Command Line Interface

#### List Available Ports

```bash
python main.py list
```

#### Run a Countdown

```bash
python main.py countdown --port 0 --seconds 10 --baudrate 9600
```

Or with short options:

```bash
python main.py countdown -p 0 -s 10 -b 9600
```

### Web Application

The project includes a web interface for controlling the LED display.

#### Running the Web App

```bash
python run_web_app.py
```

Then open your browser and navigate to:

```
http://localhost:8080
```

The web interface allows you to:
- Select from available USB serial ports
- Set the countdown duration
- Start the countdown with a button click
- See the status of the countdown operation

## Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
