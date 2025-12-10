"""
Script to run a Phaser device with Firebase edge service.
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
from time import sleep
from typing import Optional
from src.edge.edge_phaser_controller import EdgePhaserController
from adi import ad9361
from adi.cn0566 import CN0566
from src.ws.ws_edge_service import WsEdgeService
from start_phaser_interface import startPhaserInterface

def main():
    """Main function to set up and run the real Pluto with Firebase edge service."""
    
    # Configuration
    device_id = createId(10)
    poll_interval = 10.0  # seconds
    
    print(f"Starting Phaser Pluto Device with ID: {device_id}")
    print("=" * 50)

    # First try to connect to a locally connected CN0566. On success, connect,
    # on failure, connect to remote CN0566

    try:
        # Create phaser interface
        phaser = startPhaserInterface()
            
        ws_url = "wss://remote-gateway-ts-tgyovhjiqq-uk.a.run.app/ws"
        edge_service = WsEdgeService(
            device_id,
            ws_url,
            ssl_verify=False  # Set to False if certificate verification fails
        )
        
        # Create edge controller
        controller = EdgePhaserController(
            phaser,
            edge_service=edge_service,
            poll_s=poll_interval
        )
        
        print("    Phaser device is now running!")
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
