import string
from src.services.edge_service import EdgeService
from src.commands.commands import Command, Ack
from typing import Dict, Any, Callable, Optional


class FakeEdgeService(EdgeService):
    def publish_config(self, config: Dict[str, Any]) -> None:
        """Publish the current configuration to be read by clients."""
        pass

    def subscribe_commands(self, on_command: Callable[[Command], Ack]) -> None:
        """Register a callback for incoming commands and return acknowledgments."""
        pass

    def activate_topic(self, topicid: string) -> None:
        """Activate a topic."""
        pass

    def deactivate_topic(self, topicid: string) -> None:
        """Activate a topic."""
        pass

    def publish_topic_data(self, topicid: string, data: Dict[str, Any]) -> None:
        """Publish data to some topic."""
        pass
