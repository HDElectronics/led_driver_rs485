#!/usr/bin/env python3
"""
Main script for LED Driver RS485 project.
This script demonstrates how to use the LEDController class from the src package.
"""
import sys
import os
import time
import argparse

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Import the LEDController class from the package
from led_driver_rs485 import LEDController


def list_available_ports():
    """List all available USB serial ports."""
    ports = LEDController.scan_ports(usb_only=True)
    if not ports:
        print("No USB serial ports found.")
        return
    
    print(f"Found {len(ports)} USB serial port(s):")
    for i, port in enumerate(ports):
        print(f"  {i}: {port.device} - {port.description}")


def run_countdown(port_index, seconds, baudrate=9600):
    """Run a countdown on the specified port."""
    try:
        # Create a controller instance
        led = LEDController.from_port_list(port_index=port_index, baudrate=baudrate)
        print(f"Connected to port: {led.ser.port}")
        
        # Run the countdown
        led.countdown(address=0x01, start_seconds=seconds, play_sound=True)
        
        # Close the connection
        led.close()
        print("Connection closed.")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main function to parse arguments and run the appropriate command."""
    parser = argparse.ArgumentParser(description='LED Driver RS485 Controller')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List ports command
    list_parser = subparsers.add_parser('list', help='List available USB serial ports')
    
    # Countdown command
    countdown_parser = subparsers.add_parser('countdown', help='Run a countdown on the LED display')
    countdown_parser.add_argument('--port', '-p', type=int, default=0, 
                                help='Port index to use (default: 0)')
    countdown_parser.add_argument('--seconds', '-s', type=int, default=10, 
                                help='Countdown duration in seconds (default: 10)')
    countdown_parser.add_argument('--baudrate', '-b', type=int, default=9600, 
                                help='Baudrate for serial communication (default: 9600)')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_available_ports()
    elif args.command == 'countdown':
        run_countdown(args.port, args.seconds, args.baudrate)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
