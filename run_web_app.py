#!/usr/bin/env python3
"""
Run script for the LED Driver RS485 web application.
"""
import os
import sys
from web_app.app import app

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=8080)
