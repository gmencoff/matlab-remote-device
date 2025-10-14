#!/usr/bin/env python3
"""
Script to run a fake Pluto device with Firebase edge service.
This creates a mock Pluto SDR device and connects it to Firebase for remote control.
"""

import sys
import os
import time
import signal
from typing import Optional
from src.fakepluto import FakePluto
from src.edge.edge_pluto_controller import EdgePlutoController
from src.firebase.firebase_edge_service import FirebaseEdgeService


def main():
    """Main function to set up and run the fake Pluto with Firebase edge service."""
    
    # Configuration
    device_id = "fake-pluto-001"
    poll_interval = 1.0  # seconds
    
    print(f"Starting Fake Pluto Device with ID: {device_id}")
    print("=" * 50)
    
    try:
        # Create fake Pluto device
        fake_pluto = FakePluto()
        
        # Create Firebase edge service
        firebase_service = FirebaseEdgeService(device_id=device_id)
        
        # Create edge controller
        controller = EdgePlutoController(
            pluto_sdr=fake_pluto,
            edge_service=firebase_service,
            poll_s=poll_interval
        )
        
        print("\n🚀 Fake Pluto device is now running!")
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
            
    except Exception as e:
        print(f"❌ Error starting fake Pluto device: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Firebase credentials are properly configured")
        print("2. Check that Firebase project ID is correct")
        print("3. Ensure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    main()