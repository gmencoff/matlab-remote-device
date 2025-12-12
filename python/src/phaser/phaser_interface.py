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
            
    def set_prop(self,name,value):
        if name in self.getBaseProps():
            setattr(self,name,value)
        else:
            setattr(self._config_object,name,value)
    
    def get_prop(self,name):
        if name in self.getBaseProps():
            return getattr(self,name)
        else:
            return getattr(self._config_object,name)
        
    def getConfigProps(self):
        configProps = self._config_object.getConfigProps()
        return self.getBaseProps() + configProps
    
    def getBaseProps(self):
        return ["configuration"]
