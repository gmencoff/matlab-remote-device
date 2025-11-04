import threading, time
from typing import Any
from src.services.edge_service import EdgeService
from src.commands.commands import Command, Ack, PropertyAck, PropertySetController, ReceiveAck, ReceiveController, ReceiveStreamAck, ReceiveStreamController

class EdgePlutoController(PropertySetController, ReceiveController, ReceiveStreamController):
    """
    Controller for a Pluto SDR device on the edge.
    Handles commands from remote clients and publishes device state.
    """
    
    def __init__(self, pluto_sdr, edge_service: EdgeService, poll_s: float = 1.0):
        self._pluto = pluto_sdr
        self._edge_service = edge_service
        self._config = {}
        self._poll_s = poll_s
        self._is_streaming = False
                
        # Publish config will monitor pluto for changes and publish new configs
        self._publish_config()
        
        # Subscribe to incoming commands
        self._edge_service.subscribe_commands(self._handle_command)

    def setPropCmd(self, name: str, value: Any, id: str, ts: float) -> PropertyAck:
        try:
            # Set the property on the device
            setattr(self._pluto, name, value)
            
            # Read back the actual value (might be different from requested)
            actual_value = getattr(self._pluto, name)
            
            return PropertyAck(id, True, value=actual_value)
        except AttributeError:
            return PropertyAck(id, False, error=f"Property not found: {name}")
        except Exception as e:
            return PropertyAck(id, False, error=f"Error setting {name}: {str(e)}")

    def rxCmd(self, id: str, ts: float) -> ReceiveAck:
        try:
            
            # Get complex samples from device
            complex_samples = self._pluto.rx()
            
            # Convert complex samples to real and imaginary parts
            if hasattr(complex_samples, 'real') and hasattr(complex_samples, 'imag'):
                # Handle numpy arrays or similar
                real_samples = complex_samples.real.tolist() if hasattr(complex_samples.real, 'tolist') else list(complex_samples.real)
                imag_samples = complex_samples.imag.tolist() if hasattr(complex_samples.imag, 'tolist') else list(complex_samples.imag)
            else:
                # Handle list of complex numbers
                real_samples = [sample.real for sample in complex_samples]
                imag_samples = [sample.imag for sample in complex_samples]
            
            return ReceiveAck(id, True, real_samples=real_samples, imag_samples=imag_samples)
            
        except Exception as e:
            return ReceiveAck(id, False, error=f"Error receiving samples: {str(e)}")

    def rxStreamCmd(self, duration: float, id: str, ts: float) -> ReceiveStreamAck:
        # TODO: Start streaming samples here
        return ReceiveStreamAck(id, True)
    
    def _publish_config(self):
        """Monitor sdr for changes."""
        def loop():
            config = None
            while True:
                newconfig = self._get_current_config()
                if newconfig != config:
                    config = newconfig
                    self._edge_service.publish_config(config)
                time.sleep(self._poll_s)

        threading.Thread(target=loop, daemon=True).start()       

    def _get_current_config(self):
        config = {}
        # Get all public properties from the device
        for attr_name in self._config_props():
            # Skip private attributes and methods
            try:
                config[attr_name] = getattr(self._pluto, attr_name)
            except Exception:
                # Skip properties that can't be read
                pass
            
        return config
    
    
    def _handle_command(self, cmd: Command) -> Ack:
        """Handle an incoming command."""
        # Execute the command on the device
        ack = cmd.execute(self)
        return ack

    def _config_props(self):
        return [
            "rx_lo",
            "rx_buffer_size",
            "rx_hardwaregain_chan0",
            "rx_rf_bandwidth",
            "gain_control_mode_chan0",
            "tx_lo",
            "tx_hardwaregain_chan0",
            "tx_rf_bandwidth",
            "tx_cyclic_buffer",
            "filter",
            "sample_rate",
            "loopback"
        ]