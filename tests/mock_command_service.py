import os, json, time
from interfaces import CommandService
from utils import atomic_write_json, read_json

class MockCommandService(CommandService):
    def __init__(self,config_sync):
        self.return_ack = None
        self._config_sync = config_sync
        self.last_command = []

    def send_command(self, cmd: dict, timeout: float = 5.0) -> dict:    
        deadline = time.time() + timeout
        self.last_command = cmd
        if cmd["type"] == "property":
            self._config_sync.cfg[cmd["name"]] = cmd["value"]

        while time.time() < deadline:
            if self.return_ack is not None:
                return self.return_ack()
            time.sleep(0.1)
        raise TimeoutError(f"No ack for {cmd['id']}")

    def ack_command(self, cmd_id: str, result: dict):
        pass

    def run(self, on_command):
        pass
