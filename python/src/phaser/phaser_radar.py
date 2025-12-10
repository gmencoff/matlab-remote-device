class PhaserRadar:
    def __init__(self, phaser, sdr):
        self._phaser = phaser
        self._sdr = sdr
        self._setup_radar()
        # my_sdr = adi.ad9361(uri=sdr_ip)
        # my_phaser = adi.CN0566(uri=rpi_ip, rx_dev=my_sdr)

    def rx(self):
        return self._sdr.rx()

    @property
    def ramp_bandwidth(self):
        return self._phaser.freq_dev_range*4
    
    @ramp_bandwidth.setter
    def ramp_bandwidth(self,value):
        self._phaser.freq_dev_range = int(value/4)
    
        
    def _setup_radar(self):
        # Initialize both ADAR1000s, set gains to max, and all phases to 0
        self._phaser.configure(device_mode="rx")
        self._phaser.load_gain_cal()
        self._phaser.load_phase_cal()
        for i in range(0, 8):
            self._phaser.set_chan_phase(i, 0)
            
        gain_list = [127, 127, 127, 127, 127, 127, 127, 127]
        for i in range(0, len(gain_list)):
            self._phaser.set_chan_gain(i, gain_list[i], apply_cal=True)

        sample_rate = 0.6e6
        center_freq = 2.1e9
        signal_freq = 100e3
        num_slices = 200
        fft_size = 1024*16
        img_array = np.zeros((num_slices, fft_size))

        # Create radio
        '''This script is for Pluto Rev C, dual channel setup'''
        self._sdr.sample_rate = int(sample_rate)

        # Configure Rx
        self._sdr.rx_lo = int(center_freq)   
        self._sdr.rx_enabled_channels = [0, 1]   # enable Rx1 (voltage0) and Rx2 (voltage1)
        self._sdr.rx_buffer_size = int(fft_size)
        self._sdr.gain_control_mode_chan0 = 'manual'  # manual or slow_attack
        self._sdr.gain_control_mode_chan1 = 'manual'  # manual or slow_attack
        self._sdr.rx_hardwaregain_chan0 = int(30)   # must be between -3 and 70
        self._sdr.rx_hardwaregain_chan1 = int(30)   # must be between -3 and 70
        
        # Configure Tx
        self._sdr.tx_lo = int(center_freq)
        self._sdr.tx_enabled_channels = [0, 1]
        self._sdr.tx_cyclic_buffer = True      # must set cyclic buffer to true for the tdd burst mode.  Otherwise Tx will turn on and off randomly
        self._sdr.tx_hardwaregain_chan0 = -88   # must be between 0 and -88
        self._sdr.tx_hardwaregain_chan1 = -0   # must be between 0 and -88

        # Configure the ADF4159 Rampling PLL
        output_freq = 12.1e9
        BW = 500e6
        num_steps = 1000
        ramp_time = 500 # us
        ramp_time_s = ramp_time / 1e6
        self._phaser.frequency = int(output_freq/4) # Output frequency divided by 4
        self._phaser.freq_dev_range = int(BW/4) # frequency deviation range in Hz.  This is the total freq deviation of the complete freq ramp
        self._phaser.freq_dev_step = int(BW/num_steps) # frequency deviation step in Hz.  This is fDEV, in Hz.  Can be positive or negative
        self._phaser.freq_dev_time = int(ramp_time) # total time (in us) of the complete frequency ramp
        self._phaser.delay_word = 4095     # 12 bit delay word.  4095*PFD = 40.95 us.  For sawtooth ramps, this is also the length of the Ramp_complete signal
        self._phaser.delay_clk = 'PFD'     # can be 'PFD' or 'PFD*CLK1'
        self._phaser.delay_start_en = 0         # delay start
        self._phaser.ramp_delay_en = 0          # delay between ramps.
        self._phaser.trig_delay_en = 0          # triangle delay
        self._phaser.ramp_mode = "continuous_sawtooth"     # ramp_mode can be:  "disabled", "continuous_sawtooth", "continuous_triangular", "single_sawtooth_burst", "single_ramp_burst"
        self._phaser.sing_ful_tri = 0           # full triangle enable/disable -- this is used with the single_ramp_burst mode
        self._phaser.tx_trig_en = 0             # start a ramp with TXdata
        self._phaser.enable = 0                 # 0 = PLL enable.  Write this last to update all the registers

        # Create a uniform amplitude waveform
        N = int(self._sdr.rx_buffer_size)
        out = [1] * N

        # Send data
        self._sdr._ctx.set_timeout(0)
        self._sdr.tx([out*0.5, iq])  # only send data to the 2nd channel (that's all we need)
        
        
        
    def getConfigProps(self):
        return [
            "operating_frequency",
            "prf",
            "number_pulses",
            "sample_rate",
            "ramp_bandwidth",
            "samples_per_pulse"
        ]
    
