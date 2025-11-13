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
from phaser_interface import PhaserInterface
from adi import ad9361
from adi.cn0566 import CN0566
from src.httpservice.http_edge_service import HttpEdgeService

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
        try:
            print("Attempting to connect to CN0566 via ip:localhost...")
            my_phaser = CN0566(uri="ip:localhost")
            print("Found CN0566. Connecting to PlutoSDR via default IP address...")
            my_sdr = ad9361(uri="ip:192.168.2.1")
            print("PlutoSDR connected.")

        except:
            print("CN0566 on ip.localhost not found, connecting via ip:phaser.local...")
            my_phaser = CN0566(uri="ip:phaser.local")
            print("Found CN0566. Connecting to PlutoSDR via shared context...")
            my_sdr = ad9361(uri="ip:phaser.local:50901")
            print("Found SDR on shared phaser.local.")

        my_phaser.sdr = my_sdr  # Set my_phaser.sdr

        sleep(0.5)

        # By default device_mode is "rx"
        my_phaser.configure(device_mode="rx")
        my_phaser.SignalFreq = 10.525e9


        # Configure CN0566 parameters.
        #     ADF4159 and ADAR1000 array attributes are exposed directly, although normally
        #     accessed through other methods.


        # Set all antenna elements to half scale - a typical HB100 will have plenty
        # of signal power.

        gain_list = [64] * 8  # (64 is about half scale)
        for i in range(0, len(gain_list)):
            my_phaser.set_chan_gain(i, gain_list[i], apply_cal=False)

        # Aim the beam at boresight (zero degrees). Place HB100 right in front of array.
        my_phaser.set_beam_phase_diff(0.0)


        #  Configure SDR parameters. Start with the more involved settings, don't
        # pay too much attention to these. They are covered in much more detail in
        # Software Defined Radio for Engineers.

        my_sdr._ctrl.debug_attrs["adi,frequency-division-duplex-mode-enable"].value = "1"
        my_sdr._ctrl.debug_attrs[
            "adi,ensm-enable-txnrx-control-enable"
        ].value = "0"  # Disable pin control so spi can move the states
        my_sdr._ctrl.debug_attrs["initialize"].value = "1"

        my_sdr.rx_enabled_channels = [0, 1]  # enable Rx1 (voltage0) and Rx2 (voltage1)
        my_sdr._rxadc.set_kernel_buffers_count(1)  # No stale buffers to flush
        rx = my_sdr._ctrl.find_channel("voltage0")
        rx.attrs["quadrature_tracking_en"].value = "1"  # enable quadrature tracking
        # Make sure the Tx channels are attenuated (or off) and their freq is far away from Rx
        # this is a negative number between 0 and -88
        my_sdr.tx_hardwaregain_chan0 = int(-80)
        my_sdr.tx_hardwaregain_chan1 = int(-80)


        # These parameters are more closely related to analog radio design
        # and are what you would adjust to change the IFs, signal bandwidths, sample rate, etc.
        #
        # Sample rate is set to 30Msps,
        # for a total of 30MHz of bandwidth (quadrature sampling)
        # Filter is 20MHz LTE, so you get a bit less than 20MHz of usable
        # bandwidth.

        my_sdr.sample_rate = 30e6  # Sampling rate
        my_sdr.rx_buffer_size = int(1024)  # Number of samples per buffer
        my_sdr.rx_rf_bandwidth = int(10e6)  # Analog bandwidth

        # Manually control gain - in most applications, you want to enable AGC to keep
        # to adapt to changing conditions. Since we're taking quasi-quantitative measurements,
        # we want to set the gain to a fixed value.
        my_sdr.gain_control_mode_chan0 = "manual"  # DISable AGC
        my_sdr.gain_control_mode_chan1 = "manual"
        my_sdr.rx_hardwaregain_chan0 = 0  # dB
        my_sdr.rx_hardwaregain_chan1 = 0  # dB

        my_sdr.rx_lo = int(2.2e9)  # Downconvert by 2GHz  # Receive Freq

        # Now set the phaser's PLL. This is the ADF4159, and we'll set it to the HB100 frequency
        # plus the desired 2GHz IF, minus a small offset so we don't land at exactly DC.
        # If the HB100 is at exactly 10.525 GHz, setting the PLL to 12.724 GHz will result
        # in an IF at 2.201 GHz.

        offset = 1000000  # add a small offset
        my_phaser.frequency = (
            int(my_phaser.SignalFreq + my_sdr.rx_lo - offset)
        ) // 4  # PLL feedback is from the VCO's /4 output
            
        # Create Firebase edge service
        firebase_service = HttpEdgeService(device_id=device_id)
        
        # Create phaser interface
        phaser = PhaserInterface(my_phaser,my_sdr)
        
        # Create edge controller
        controller = EdgePhaserController(
            phaser,
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
