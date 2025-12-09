class PhaserInterface:
    """
    Wrapper around the components of the phaser to provide a simpler interface.
    """
    
    def __init__(self, phaser, sdr):
        self._phaser = phaser
        self._sdr = sdr
        
    def rx(self):
        return self._sdr.rx()
        
    @property
    def sample_rate(self):
        return self._sdr.sample_rate
    
    @sample_rate.setter
    def sample_rate(self, value):
        self._sdr_sample_rate = int(value)
        
    @property
    def rx_buffer_size(self):
        return self._sdr.rx_buffer_size
    
    @rx_buffer_size.setter
    def rx_buffer_size(self, value):
        self._sdr.rx_buffer_size = int(value)
        
    @property
    def operating_frequency(self):
        return self._phaser.SignalFreq
    
    @operating_frequency.setter
    def operating_frequency(self, value):
        self._phaser.SignalFreq = int(value)
        self._phaser.frequency = (
            self._phaser.SignalFreq + self._sdr.rx_lo
        ) // 4  # PLL feedback via /4 VCO output  
    
