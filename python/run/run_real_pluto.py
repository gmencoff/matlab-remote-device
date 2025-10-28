"""
Script to run a real Pluto device with Firebase edge service.
This creates a mock Pluto SDR device and connects it to Firebase for remote control.
"""

import sys
import os

# Add parent directory to path so 'src' imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import signal
import adi
import string
import random
from typing import Optional
from src.edge.edge_pluto_controller import EdgePlutoController
from src.httpservice.http_edge_service import HttpEdgeService


def main():
    """Main function to set up and run the real Pluto with Firebase edge service."""
    
    # Configuration
    device_id = createId(10)
    poll_interval = 10.0  # seconds
    
    print(f"Starting Real Pluto Device with ID: {device_id}")
    print("=" * 50)
    
    try:
        # Create real Pluto device
        sdr = adi.Pluto('ip:192.168.2.1')
        
        # Create Firebase edge service
        firebase_service = HttpEdgeService(device_id=device_id)
        
        # Create edge controller
        controller = EdgePlutoController(
            pluto_sdr=sdr,
            edge_service=firebase_service,
            poll_s=poll_interval
        )
        
        print("\n🚀Pluto device is now running!")
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
        
def createId(n):
    safe_chars = string.ascii_letters
    return ''.join(random.choice(safe_chars) for _ in range(n))


if __name__ == "__main__":
    main()