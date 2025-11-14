import numpy as np

class FakePhaser:
    """Shared configuration for file paths used by both client and edge services."""
    
    def __init__(self):
        self.sample_rate = 30e6
        self.rx_buffer_size = 1024
    
    def rx(self):
        ch1 = np.random.randn(self.rx_buffer_size) + 1j * np.random.randn(self.rx_buffer_size)
        ch2 = np.random.randn(self.rx_buffer_size) + 1j * np.random.randn(self.rx_buffer_size)
        return [ch1,ch2] 
