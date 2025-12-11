from src.phaser.phaser_radar import PhaserRadar

class PhaserInterface:
    """
    Wrapper around the components of the phaser to provide a simpler interface.
    """
    
    def __init__(self, phaser, sdr, tdd, sdr_pins):
        self._phaser = phaser
        self._sdr = sdr
        self._tdd = tdd
        self._sdr_pins = sdr_pins
        self.configuration = 'radar'
        
    def rx(self):
        return self._config_object.rx()
    
    @property
    def configuration(self):
        return self._configuration
    
    @configuration.setter
    def configuration(self,value):
        if value == "radar" or value == "radio":
            self._configuration = value
            self._setup_config_object()
        else:
            raise ValueError('Configuration must be set to "radio" or "radar"')
        
    def _setup_config_object(self):
        if self.configuration == "radar":
            self._config_object = PhaserRadar(self._phaser,self._sdr,self._tdd,self._sdr_pins)
        elif self.configuration == "radio":
            self._config_object = [] # TODO    
    
    def get(self,name):
        if name in self.getBaseProps():
            return getattr(self,name)
        else:
            return getattr(self._config_object,name)
        
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
        
    def getConfigProps(self):
        configProps = self._config_object.getConfigProps()
        return self.getBaseProps() + configProps
    
    def getBaseProps(self):
        return ["configuration"]
