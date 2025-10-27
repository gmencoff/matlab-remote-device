#!/usr/bin/env python3
"""
Entry point script to run the fake Pluto device.
This script should be run from the python/ directory with the virtual environment activated.

Usage:
    cd /Users/georgemencoff/Desktop/pluto-data-streaming/python
    source venv/bin/activate
    python run_fake_pluto.py
"""

import sys
import os

# Add the current directory to Python path so 'src' imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import and run the main function
from src.runfakepluto import main

if __name__ == "__main__":
    main()
