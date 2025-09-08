from commands import Command, CommandType
from interfaces import ClientService
from typing import Dict, Any, Callable

class MockClientService(ClientService):
    def __init__(self,cfg):
        self.cfg = cfg
        self.last_command = []
        self.send_property_ack = {"ok": True}

    def send_command(self, cmd: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:    
        self.last_command = cmd
        return self.send_property_ack

    def subscribe_config(self, on_change: Callable[[Dict[str, Any]], None]) -> None:
        self.config_change_callback = on_change
        self.send_config_change()

    def update_config(self, property, value):
        self.cfg[property] = value
        self.send_config_change()

    def send_config_change(self):
        self.config_change_callback(self.cfg)