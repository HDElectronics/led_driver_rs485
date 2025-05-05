#!/usr/bin/env python3
"""
Flask web application for LED Driver RS485 Controller.
"""
import sys
import os
import time
import json
import threading
from flask import Flask, render_template, request, jsonify

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the LEDController class from the package
from led_driver_rs485 import LEDController

app = Flask(__name__)

# Global variable to store the current countdown thread
countdown_thread = None
countdown_running = False

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/ports', methods=['GET'])
def get_ports():
    """Get a list of available USB serial ports."""
    try:
        ports = LEDController.scan_ports(usb_only=True)
        port_list = []

        for i, port in enumerate(ports):
            port_list.append({
                'index': i,
                'device': port.device,
                'description': port.description
            })

        return jsonify({
            'success': True,
            'ports': port_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/countdown', methods=['POST'])
def start_countdown():
    """Start a countdown on the specified port."""
    global countdown_thread, countdown_running

    # Check if a countdown is already running
    if countdown_thread and countdown_thread.is_alive():
        return jsonify({
            'success': False,
            'error': 'A countdown is already running'
        }), 400

    # Get parameters from the request
    data = request.json
    port_index = int(data.get('port_index', 0))
    seconds = int(data.get('seconds', 10))
    baudrate = int(data.get('baudrate', 9600))

    # Start the countdown in a separate thread
    countdown_running = True
    countdown_thread = threading.Thread(
        target=run_countdown_thread,
        args=(port_index, seconds, baudrate)
    )
    countdown_thread.daemon = True
    countdown_thread.start()

    return jsonify({
        'success': True,
        'message': f'Countdown started for {seconds} seconds on port {port_index}'
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get the current status of the countdown."""
    global countdown_thread, countdown_running

    if countdown_thread and countdown_thread.is_alive():
        status = 'running'
    else:
        status = 'idle'
        countdown_running = False

    return jsonify({
        'success': True,
        'status': status,
        'running': countdown_running
    })

def run_countdown_thread(port_index, seconds, baudrate):
    """Run a countdown on the specified port in a separate thread."""
    global countdown_running

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
    finally:
        countdown_running = False

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
