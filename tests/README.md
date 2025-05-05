# Unit Tests for LED Driver RS485

This directory contains unit tests for the LED Driver RS485 project.

## Running the Tests

To run the tests, you need to install the required dependencies first:

```bash
pip install -r requirements.txt
```

Then, you can run the tests using pytest:

```bash
pytest
```

Or to run with more detailed output:

```bash
pytest -v
```

## Test Coverage

The tests cover the following functionality:

1. CRC16 calculation
2. Command building
3. Command sending (with mocked serial port)
4. Display content functionality
5. Countdown functionality
6. Port scanning
7. Controller initialization from port list

## Mocking Hardware

Since the code communicates with physical hardware (USB TTL RS485 adapter), the tests use mocking to simulate the hardware responses. This allows testing the code without requiring the actual hardware to be connected.

## Adding More Tests

To add more tests, simply add new test methods to the `TestLEDController` class in `test_led_driver_rs485.py`. Make sure to follow the naming convention (`test_*`) for test methods.
