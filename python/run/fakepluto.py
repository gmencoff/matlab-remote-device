import numpy as np

class FakePluto:
    """Shared configuration for file paths used by both client and edge services."""
    
    def __init__(self):
        self.sample_rate = 30e6
        self.rx_buffer_size = 1024
    
    def rx(self):
        return np.random.randn(self.rx_buffer_size) + 1j * np.random.randn(self.rx_buffer_size)