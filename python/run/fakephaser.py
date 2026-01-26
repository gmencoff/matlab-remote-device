import numpy as np
from src.phaser.phaser_interface import PhaserInterface

class FakePhaser(PhaserInterface):
    """Shared configuration for file paths used by both client and edge services."""
    
    def __init__(self):
        self.sample_rate = 30e6
        self.rx_buffer_size = 1024
    
    def rx(self):
        ch1 = np.random.randn(self.rx_buffer_size) + 1j * np.random.randn(self.rx_buffer_size)
        ch2 = np.random.randn(self.rx_buffer_size) + 1j * np.random.randn(self.rx_buffer_size)
        return [ch1,ch2]
    
    def set_prop(self,name,value):
        # Set a property on the device
        setattr(self,name,value)

    def get_prop(self,name):
        # Get a property from the device
        return getattr(self,name)

    def getConfigProps(self):
        return ["sample_rate","rx_buffer_size"]
