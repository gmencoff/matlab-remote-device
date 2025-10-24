import threading, time
from src.services.edge_service import EdgeService
from src.commands.commands import Command, Ack

class EdgePlutoController:
    """
    Controller for a Pluto SDR device on the edge.
    Handles commands from remote clients and publishes device state.
    """
    
    def __init__(self, pluto_sdr, edge_service: EdgeService, config_props, poll_s: float = 1.0):
        self._pluto = pluto_sdr
        self._edge_service = edge_service
        self._config_props = config_props
        self._config = {}
        self._poll_s = poll_s
                
        # Publish config will monitor pluto for changes and publish new configs
        self._publish_config()
        
        # Subscribe to incoming commands
        self._edge_service.subscribe_commands(self._handle_command)
    
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
        for attr_name in self._config_props:
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
        ack = cmd.execute(self._pluto)
        return ack