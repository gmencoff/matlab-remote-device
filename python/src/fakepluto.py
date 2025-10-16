import numpy as np

class FakePluto:
    """Shared configuration for file paths used by both client and edge services."""
    
    def __init__(self):
        self.sample_rate = 30e6
    
    def rx(self):
        n = 1024
        return np.random.randn(n) + 1j * np.random.randn(n)