from abc import ABC, abstractmethod
from typing import Dict, Any, Callable

class ClientService(ABC):
    @abstractmethod
    def send_command(self, cmd: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
        """Send a command and block until ack is received."""
        pass

    @abstractmethod
    def subscribe_config(self, on_change: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback for config changes."""
        pass
