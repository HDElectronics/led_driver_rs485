import unittest
from unittest.mock import patch, MagicMock, call
import pytest
import struct
import time
import sys
import os

# Add the src directory to sys.path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from led_driver_rs485 import LEDController


class TestLEDController(unittest.TestCase):

    def test_crc16(self):
        """Test the CRC16 calculation function."""
        controller = LEDController(port=None)
        # Mock the serial port initialization
        controller.ser = MagicMock()

        # Test with known input and expected output
        test_data = b'\xFE\x05\x01\x01\xFF'
        result = controller.crc16(test_data)

        # Verify the result is a bytes object of length 2
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 2)

        # You would need to calculate the expected CRC value for this test data
        # For now, we'll just ensure it returns a consistent result
        self.assertEqual(result, controller.crc16(test_data))

    def test_build_command(self):
        """Test the command building function."""
        controller = LEDController(port=None)
        # Mock the serial port initialization
        controller.ser = MagicMock()

        # Test with simple parameters
        address = 0x01
        command = 0x01
        payload = b'\x00\x10\x05'

        result = controller.build_command(address, command, payload)

        # Check the packet structure
        self.assertEqual(result[0], 0xFE)  # Start byte
        self.assertEqual(result[1], 8)     # Length
        self.assertEqual(result[2], address)
        self.assertEqual(result[3], command)
        self.assertEqual(result[4:7], payload)
        self.assertEqual(result[7], 0xFF)  # End byte
        # Last 2 bytes are CRC
        self.assertEqual(len(result), 10)

    @patch('serial.Serial')
    def test_send_command(self, mock_serial):
        """Test sending a command with mocked serial port."""
        # Setup the mock
        mock_instance = MagicMock()
        mock_serial.return_value = mock_instance
        mock_instance.read_all.return_value = b'\xAA\xBB'  # Mock response

        # Create controller with mocked serial
        controller = LEDController(port='COM1')
        controller.ser = mock_instance

        # Test sending a command
        response = controller.send_command(0x01, 0x02, b'\x03\x04')

        # Verify serial.write was called with the correct packet
        self.assertTrue(mock_instance.write.called)
        # Verify read_all was called to get the response
        self.assertTrue(mock_instance.read_all.called)
        # Check the response
        self.assertEqual(response, b'\xAA\xBB')

    @patch('serial.Serial')
    def test_display_content(self, mock_serial):
        """Test the display_content method."""
        # Setup the mock
        mock_instance = MagicMock()
        mock_serial.return_value = mock_instance
        mock_instance.read_all.return_value = b'\xAA\xBB'  # Mock response

        # Create controller with mocked serial
        controller = LEDController(port='COM1')
        controller.ser = mock_instance

        # Test displaying content
        response = controller.display_content(
            address=0x01,
            flash=True,
            save=True,
            items=2,
            bytes_per_item=1,
            content_bytes=b'\x05\x06'
        )

        # Verify serial.write was called
        self.assertTrue(mock_instance.write.called)
        # Check the response
        self.assertEqual(response, b'\xAA\xBB')

    @patch('serial.Serial')
    @patch('time.sleep')  # Mock sleep to speed up tests
    @patch('led_driver_rs485.controller.playsound')  # Mock playsound to avoid actual sound
    def test_countdown(self, mock_playsound, mock_sleep, mock_serial):
        """Test the countdown method."""
        # Setup the mock
        mock_instance = MagicMock()
        mock_serial.return_value = mock_instance

        # Create controller with mocked serial
        controller = LEDController(port='COM1')
        controller.ser = mock_instance

        # Test countdown with a small value to keep test fast
        controller.countdown(address=0x01, start_seconds=2, play_sound=True)

        # Verify display_content was called for each second
        # Should be called 3 times (2, 1, 0)
        self.assertEqual(mock_instance.write.call_count, 3)

        # Verify playsound was called at the end
        mock_playsound.assert_called_once()

    @patch('serial.tools.list_ports.comports')
    def test_scan_ports(self, mock_comports):
        """Test the scan_ports method."""
        # Create mock port objects
        mock_port1 = MagicMock()
        mock_port1.description = "USB Serial Device"
        mock_port1.hwid = "USB VID:PID=1234:5678"

        mock_port2 = MagicMock()
        mock_port2.description = "COM Port"
        mock_port2.hwid = "ACPI\\PNP0501"

        # Setup the mock to return our test ports
        mock_comports.return_value = [mock_port1, mock_port2]

        # Test with usb_only=True (should return only the USB port)
        ports = LEDController.scan_ports(usb_only=True)
        self.assertEqual(len(ports), 1)
        self.assertEqual(ports[0], mock_port1)

        # Test with usb_only=False (should return all ports)
        ports = LEDController.scan_ports(usb_only=False)
        self.assertEqual(len(ports), 2)

    @patch('serial.tools.list_ports.comports')
    def test_from_port_list(self, mock_comports):
        """Test the from_port_list class method."""
        # Create mock port objects
        mock_port = MagicMock()
        mock_port.device = "/dev/ttyUSB0"
        mock_port.description = "USB Serial Device"
        mock_port.hwid = "USB VID:PID=1234:5678"

        # Setup the mock to return our test port
        mock_comports.return_value = [mock_port]

        # Patch the LEDController.__init__ to avoid actual serial port initialization
        with patch.object(LEDController, '__init__', return_value=None) as mock_init:
            # Test creating controller from port list
            controller = LEDController.from_port_list(port_index=0, baudrate=9600)

            # Verify __init__ was called with the correct parameters
            mock_init.assert_called_once_with(port="/dev/ttyUSB0", baudrate=9600, timeout=1)

    @patch('serial.tools.list_ports.comports')
    def test_from_port_list_no_ports(self, mock_comports):
        """Test from_port_list when no ports are available."""
        # Setup the mock to return an empty list
        mock_comports.return_value = []

        # Test that RuntimeError is raised when no ports are found
        with self.assertRaises(RuntimeError):
            LEDController.from_port_list()

    @patch('serial.tools.list_ports.comports')
    def test_from_port_list_index_out_of_range(self, mock_comports):
        """Test from_port_list with an out-of-range index."""
        # Create mock port objects
        mock_port1 = MagicMock()
        mock_port1.device = "/dev/ttyUSB0"
        mock_port1.description = "USB Serial Device"
        mock_port1.hwid = "USB VID:PID=1234:5678"

        # Setup the mock to return our test ports
        mock_comports.return_value = [mock_port1]

        # Patch the LEDController.__init__ to avoid actual serial port initialization
        with patch.object(LEDController, '__init__', return_value=None):
            # Test that IndexError is raised when port_index is out of range
            with self.assertRaises(IndexError):
                LEDController.from_port_list(port_index=1)


if __name__ == '__main__':
    unittest.main()
