#!/usr/bin/env python3
"""
Script to run a fake Phaser device with Firebase edge service.
This creates a mock Phaser device and connects it to Firebase for remote control.
"""

import sys
import os

# Add parent directory to path so 'src' imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import signal
from typing import Optional
from fakephaser import FakePhaser
from src.edge.edge_phaser_controller import EdgePhaserController
from src.httpservice.http_edge_service import HttpEdgeService
from fake_edge_service import FakeEdgeService
from start_phaser_interface import startPhaserInterface


def main():
    """Main function to set up and run the fake Pluto with Firebase edge service."""
    
    # Configuration
    device_id = "fake-phaser-001"
    poll_interval = 1.0  # seconds
    
    print(f"Starting Fake Pluto Device with ID: {device_id}")
    print("=" * 50)

    # Create fake Pluto device
    phaser = FakePhaser()
    
    # Create Firebase edge service
    edge_service = HttpEdgeService(device_id)
    
    # Create edge controller
    controller = EdgePhaserController(
        phaser,
        edge_service=edge_service,
        poll_s=poll_interval
    )
    
    print(f"   Phaser device is now running!")
    print(f"   Device ID: {device_id}")
    print(f"   Polling interval: {poll_interval}s")
    print("   Listening for commands via Firebase...")
    print("\nPress Ctrl+C to stop the device")
    print("-" * 50)
    
    # Keep the main thread alive
    def signal_handler(sig, frame):
        print("\n\n🛑 Shutting down fake Pluto device...")
        print("✓ Device stopped")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Main loop - just keep alive
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
