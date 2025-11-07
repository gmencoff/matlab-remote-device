from abc import ABC, abstractmethod
import string
from typing import Dict, Any, Callable
from src.commands.commands import Command, Ack

class EdgeService(ABC):
    @abstractmethod
    def publish_config(self, config: Dict[str, Any]) -> None:
        """Publish the current configuration to be read by clients."""
        pass

    @abstractmethod
    def subscribe_commands(self, on_command: Callable[[Command], Ack]) -> None:
        """Register a callback for incoming commands and return acknowledgments."""
        pass

    @abstractmethod
    def activate_topic(self, topicid: string) -> None:
        """Activate a topic."""
        pass

    @abstractmethod
    def deactivate_topic(self, topicid: string) -> None:
        """Activate a topic."""
        pass

    @abstractmethod
    def publish_topic_data(self, topicid: string, data: Dict[str, Any]) -> None:
        """Publish data to some topic."""
        pass
