import time
import signal
import adi
import string
import random
from time import sleep
from typing import Optional
from adi import ad9361
from adi.cn0566 import CN0566
from src.phaser.phaser_interface import PhaserInterface

def startPhaserInterface():
    try:
        rpi_ip = "ip:phaser.local"  # IP address of the Raspberry Pi
        sdr_ip = "ip:192.168.2.1"  # "192.168.2.1, or pluto.local"  # IP address of the Transceiver Block
        my_sdr = adi.ad9361(uri=sdr_ip)
        my_phaser = adi.CN0566(uri=rpi_ip, sdr=my_sdr)
        tdd = adi.tddn(sdr_ip)
        sdr_pins = adi.one_bit_adc_dac(sdr_ip)

    except:
        print("Error setting up device")

    sleep(0.5)
    
    # Return phaser interface
    return PhaserInterface(my_phaser,my_sdr,tdd,sdr_pins)
