class MockPluto:
    def __init__(self):
        # do nothing on init
        self.cfg = {
            "rx_lo": 2.4e9,
            "sample_rate": 30e6,
            "rx_buffer_size": 4096,
        }
        self._subscribe_cb = None

    def read_config(self):
        return self.cfg

    def write_config(self, cfg: dict):
        self.cfg = cfg

    def subscribe(self, on_change):
        self._subscribe_cb = on_change

    def call_subscribe_cb(self, cfg: dict):
        self._subscribe_cb(cfg)