from typing import Dict, Any, Callable
from src.services.edge_service import EdgeService
from src.commands.commands import Command, Ack


class ApsEdgeService(EdgeService):
    """
    Edge service using Mathworks APS.
    """

    def __init__(self, device_id: str):
        """
        Initialize the APS service.
        """
        self.device_id = device_id

    def publish_config(self, config: Dict[str, Any]) -> None:
        """Implement publish config function."""
        self._current_config = config
        
        config_message = {
            "type": "setConfig",
            "deviceId": self.device_id,
            "config": config
        }
        
        # TODO: use aps to publish config

    def subscribe_commands(self, on_command: Callable[[Command], Ack]) -> None:
        """
        Register a callback for incoming commands from the server via WebSocket.
        When a command is received, it calls the on_command callback 
        and sends the acknowledgment back via WebSocket.
        
        Args:
            on_command: Callback function that processes commands and returns acknowledgments
        """
        self._on_command_callback = on_command

        # TODO: subscribe commands using APS
    
    def activate_topic(self, topicid: str) -> None:
        """Activate a topic (no-op for now)."""
        pass

    def deactivate_topic(self, topicid: str) -> None:
        """Deactivate a topic (no-op for now)."""
        pass

    def publish_topic_data(self, topicid: str, data: Dict[str, Any]) -> None:
        """Publish data to a topic (no-op for now)."""
        pass
