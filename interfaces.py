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



class ConfigSync(ABC):
    """Abstract interface for reading/writing shared config."""

    @abstractmethod
    def read_config(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def write_config(self, cfg: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def subscribe(self, on_change: Callable[[Dict[str, Any]], None]) -> None:
        """Call on_change whenever config changes"""
        pass


class CommandService(ABC):
    """Abstract interface for sending/receiving commands."""

    @abstractmethod
    def send_command(self, cmd: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
        pass

    @abstractmethod
    def ack_command(self, cmd_id: str, result: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def run(self, on_command) -> None:
        """Edge-only: continuously receive commands and call handler(cmd)."""
        pass
