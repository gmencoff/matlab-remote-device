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
from fake_edge_service import FakeEdgeService
#import matplotlib.pyplot as plt
from src.data.complex_number import ComplexNumberArray

def main():
    """Main function to set up and run the real Pluto with Firebase edge service."""
    
    # Configuration
    device_id = createId(10)
    poll_interval = 10.0  # seconds

    # First try to connect to a locally connected CN0566. On success, connect,
    # on failure, connect to remote CN0566

    # Create phaser interface
    phaser = startPhaserInterface()
    
    # Set the number of chirps
    phaser.set_prop('sample_rate',700e3)
    #a = phaser.get_prop('number_chirps')
    
    data = phaser.rx()
    cn = ComplexNumberArray(data)
    print(cn.to_dict()["real_samples"])
    
    #a = phaser.get_prop('number_chirps')
    #print(a)
    
    # Create edge controller
#     edge_service = FakeEdgeService()
#     controller = EdgePhaserController(
#         phaser,
#         edge_service=edge_service,
#         poll_s=poll_interval
#     )
#     
#     # Call the receive command on the controller
#     ack = controller.rxCmd('abc',123)
#     print(ack.data.to_dict())

def createId(n):
    safe_chars = string.ascii_letters
    return ''.join(random.choice(safe_chars) for _ in range(n))


if __name__ == "__main__":
    main()
