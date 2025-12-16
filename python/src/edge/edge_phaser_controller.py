import threading, time
from typing import Any
import numpy as np
from src.services.edge_service import EdgeService
from src.commands.commands import Command, Ack, PropertyAck, PropertySetController, ReceiveAck, ReceiveController, ReceiveStreamAck
from src.data.complex_number import ComplexNumberArray

class EdgePhaserController(PropertySetController, ReceiveController):
    """
    Controller for the Phaser board on the edge.
    """
    
    def __init__(self, phaser, edge_service: EdgeService, poll_s: float = 1.0):
        self._phaser = phaser
        self._edge_service = edge_service
        self._config = {}
        self._poll_s = poll_s
                
        # Publish config will monitor phaser for changes and publish new configs
        self._publish_config()
        
        # Subscribe to incoming commands
        self._edge_service.subscribe_commands(self._handle_command)

    def setPropCmd(self, name: str, value: Any, id: str, ts: float) -> PropertyAck:
        try:
            # Set the property on the device
            self._phaser.set_prop(name, value)
            
            # Read back the actual value (might be different from requested)
            actual_value = self._phaser.get_prop(name)
            
            return PropertyAck(id, True, value=actual_value)
        except AttributeError:
            return PropertyAck(id, False, error=f"Property not found: {name}")
        except Exception as e:
            return PropertyAck(id, False, error=f"Error setting {name}: {str(e)}")

    def rxCmd(self, id: str, ts: float) -> ReceiveAck:
        try:
            
            data = self._rx_samples();
            
            return ReceiveAck(id, True, data=data)
        except Exception as e:
            return ReceiveAck(id, False, error=f"Error receiving samples: {str(e)}")
    
    def _publish_config(self):
        """Monitor device for changes."""
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
                config[attr_name] = self._phaser.get_prop(attr_name)
            except Exception:
                # Skip properties that can't be read
                pass
            
        return config
    
    
    def _handle_command(self, cmd: Command) -> Ack:
        """Handle an incoming command."""
        # Execute the command on the device
        ack = cmd.execute(self)
        return ack

    def _rx_samples(self):
        # Get complex samples from device
        # TODO: Implement this - get the samples from the underlying devices
        # Read from device
        complex_samples = self._phaser.rx()
        return ComplexNumberArray(complex_samples=complex_samples)


    def _config_props(self):
        return self._phaser.getConfigProps()