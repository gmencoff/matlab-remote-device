import numpy as np

class PhaserRadar:
    def __init__(self, phaser, sdr, tdd, sdr_pins):
        # Save Phaser interfaces and set it up as a radar
        self._phaser = phaser
        self._sdr = sdr
        self._tdd = tdd
        self._sdr_pins = sdr_pins
        self._setup_radar()
        
        # Set properties specific to this interface that are not configured in the underlying devices
        self.samples_per_pulse = 100

    def rx(self):
        self._phaser._gpios.gpio_burst = 0
        self._phaser._gpios.gpio_burst = 1
        self._phaser._gpios.gpio_burst = 0
        data = self._sdr.rx()
        return self._create_data_cube(data)
    
    def _create_data_cube(self,data):
        # Rearrange the data cube based on the set number of samples and chirps.
        
        # Get the number of samples from start of ramp that we should offset our collection
        begin_offset_time = 0.10 * self.ramp_time   # time in seconds
        start_offset_time = self._tdd.channel[0].on_ms/1e3 + begin_offset_time
        start_offset_samples = int(start_offset_time * self.sample_rate)
        
        # Get the number of samples per frame
        frame_length = 1/self.prf
        samples_per_frame = int(frame_length * self.sample_rate)

        # Get the number of samples and the number of pulses
        num_samples = self.samples_per_pulses
        num_pulses = self.number_chirps
        
        cube = np.zeros((num_samples, 2, num_pulses), dtype=complex)
        for burst in range(num_pulses):
            start_index = start_offset_samples + burst*samples_per_frame
            stop_index = start_index + num_samples
            din = data[start_index:stop_index]
            cube[:,:,burst] = din
        
    return cube

    @property
    def ramp_bandwidth(self):
        return self._phaser.freq_dev_range*4
    
    @ramp_bandwidth.setter
    def ramp_bandwidth(self,value):
        self._phaser.freq_dev_range = int(value/4)
        
    @property
    def ramp_time(self):
        return self._phaser.freq_dev_time / 1e6
    
    @ramp_time.setter
    def ramp_time(self,value):
        self._phaser.freq_dev_time = int(value*1e6)
        
    @property
    def sample_rate(self):
        return self._sdr.sample_rate
    
    @sample_rate.setter
    def sample_rate(self,value):
        self._sdr.sample_rate = int(value)  
        
    @property
    def number_chirps(self):
        return self._tdd.burst_count
    
    @number_chirps.setter
    def number_chirps(self,value):
        self._tdd.burst_count = int(value)
        
    @property    
    def prf(self):
        frame_length = self._tdd.frame_length_ms/1e3
        return 1 / frame_length
    
    @prf.setter
    def prf(self,value):
        frame_length = 1/value
        self._tdd.frame_length_ms = frame_length*1e3
        
    def _setup_radar(self):
        # Default parameters
        sample_rate = 5e6
        center_freq = 2.1e9
        signal_freq = 100e3
        rx_gain = 20
        output_freq = 9.8e9
        default_chirp_bw = 500e6
        ramp_time = 500 #us
        num_chirps = 1

        # Initialize both ADAR1000s, set gains to max, and all phases to 0
        self._phaser.configure(device_mode="rx")
        self._phaser.element_spacing = 0.014
        self._phaser.load_gain_cal()
        self._phaser.load_phase_cal()
        for i in range(0, 8):
            self._phaser.set_chan_phase(i, 0)

        gain_list = [127] * 8
        for i in range(0, len(gain_list)):
            self._phaser.set_chan_gain(i, gain_list[i], apply_cal=True)

        # Setup Raspberry Pi GPIO states
        self._phaser._gpios.gpio_tx_sw = 0  # 0 = TX_OUT_2, 1 = TX_OUT_1
        self._phaser._gpios.gpio_vctrl_1 = 1 # 1=Use onboard PLL/LO source  (0=disable PLL and VCO, and set switch to use external LO input)
        self._phaser._gpios.gpio_vctrl_2 = 1 # 1=Send LO to transmit circuitry  (0=disable Tx path, and send LO to LO_OUT)

        # Configure SDR Rx
        self._sdr.sample_rate = int(sample_rate)
        self._sdr.rx_lo = int(center_freq)
        self._sdr.rx_enabled_channels = [0, 1]  # enable Rx1 and Rx2
        self._sdr.gain_control_mode_chan0 = "manual"  # manual or slow_attack
        self._sdr.gain_control_mode_chan1 = "manual"  # manual or slow_attack
        self._sdr.rx_hardwaregain_chan0 = int(rx_gain)  # must be between -3 and 70
        self._sdr.rx_hardwaregain_chan1 = int(rx_gain)  # must be between -3 and 70

        # Configure SDR Tx
        self._sdr.tx_lo = int(center_freq)
        self._sdr.tx_enabled_channels = [0, 1]
        self._sdr.tx_cyclic_buffer = True  # must set cyclic buffer to true for the tdd burst mode.
        self._sdr.tx_hardwaregain_chan0 = -88  # must be between 0 and -88
        self._sdr.tx_hardwaregain_chan1 = -0  # must be between 0 and -88

        # Configure the ADF4159 Ramping PLL
        vco_freq = int(output_freq + signal_freq + center_freq)
        BW = default_chirp_bw
        num_steps = int(ramp_time)    # in general it works best if there is 1 step per us
        self._phaser.frequency = int(vco_freq / 4)
        self._phaser.freq_dev_range = int(BW / 4)      # total freq deviation of the complete freq ramp in Hz
        self._phaser.freq_dev_step = int((BW / 4) / num_steps)  # This is fDEV, in Hz.  Can be positive or negative
        self._phaser.freq_dev_time = int(ramp_time)  # total time (in us) of the complete frequency ramp
        self._phaser.delay_word = 4095  # 12 bit delay word.  4095*PFD = 40.95 us.  For sawtooth ramps, this is also the length of the Ramp_complete signal
        self._phaser.delay_clk = "PFD"  # can be 'PFD' or 'PFD*CLK1'
        self._phaser.delay_start_en = 0  # delay start
        self._phaser.ramp_delay_en = 0  # delay between ramps.
        self._phaser.trig_delay_en = 0  # triangle delay
        self._phaser.ramp_mode = "single_sawtooth_burst"  # ramp_mode can be:  "disabled", "continuous_sawtooth", "continuous_triangular", "single_sawtooth_burst", "single_ramp_burst"
        self._phaser.sing_ful_tri = 0  # full triangle enable/disable -- this is used with the single_ramp_burst mode
        self._phaser.tx_trig_en = 1  # start a ramp with TXdata
        self._phaser.enable = 0  # 0 = PLL enable.  Write this last to update all the registers

        # %%
        """ Synchronize chirps to the start of each Pluto receive buffer
        """
        # Configure TDD controller
        self._sdr_pins.gpio_tdd_ext_sync = True # If set to True, this enables external capture triggering using the L24N GPIO on the Pluto.  When set to false, an internal trigger pulse will be generated every second
        self._sdr_pins.gpio_phaser_enable = True
        self._tdd.enable = False         # disable TDD to configure the registers
        self._tdd.sync_external = True
        self._tdd.startup_delay_ms = 0
        self._tdd.frame_length_ms = ramp_time/1e3 + 1.2    # each chirp is spaced this far apart
        self._tdd.burst_count = num_chirps
        self._tdd.channel[0].enable = True
        self._tdd.channel[0].polarity = False
        self._tdd.channel[0].on_ms = 0.01
        self._tdd.channel[0].off_ms = 0.1
        self._tdd.channel[1].enable = True
        self._tdd.channel[1].polarity = False
        self._tdd.channel[1].on_ms = 0.01
        self._tdd.channel[1].off_ms = 0.1
        self._tdd.channel[2].enable = False
        self._tdd.enable = True

        # Set the receive buffer size to be correct
        self._set_rx_buffer()
        
        # %%
        """ Create a sinewave waveform for Pluto's transmitter
        """
        N = int(2**18)
        fc = int(signal_freq)
        ts = 1 / float(sample_rate)
        t = np.arange(0, N * ts, ts)
        i = np.cos(2 * np.pi * t * fc) * 2 ** 14
        q = np.sin(2 * np.pi * t * fc) * 2 ** 14
        iq = 1 * (i + 1j * q)

        # transmit data from Pluto
        self._sdr._rx_init_channels()
        self._sdr.tx([iq, iq])
            
    def _set_rx_buffer(self):
        total_time = self._tdd.frame_length_ms * self.num_chirps   # time in ms
        sample_rate = self.sample_rate
        buffer_time = 0
        power=12
        while total_time > buffer_time:     
            power=power+1
            buffer_size = int(2**power) 
            buffer_time = buffer_size/sample_rate*1000   # buffer time in ms
            if power==23:
                break     # max pluto buffer size is 2**23, but for tdd burst mode, set to 2**22
        self._sdr.rx_buffer_size = buffer_size
        
    def getConfigProps(self):
        return [
            "operating_frequency",
            "prf",
            "number_chirps",
            "sample_rate",
            "ramp_bandwidth",
            "ramp_time",
            "samples_per_pulse"
        ]
    
