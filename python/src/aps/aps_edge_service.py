from typing import Dict, Any, Callable
from src.services.edge_service import EdgeService
from src.commands.commands import Command, Ack, decode_command
import src.aps.cppbridge as cppbridge
import threading
import time


class ApsEdgeService(EdgeService):
    """
    Edge service using Mathworks APS.
    """

    def __init__(self, device_id: str):
        """
        Initialize the APS service.
        """
        self.device_id = device_id
        self._running = False
        self._queue = cppbridge.CommandQueue()
        self._queue.start()

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
        if self._running:
            print("Command subscription is already running")
            return
            
        self._running = True
        self._command_thread = threading.Thread(target=self._command_listening_loop, args=(on_command,), daemon=True)
        self._command_thread.start()
        print(f"Started command listening for device {self.device_id}")

    def _command_listening_loop(self, on_command: Callable[[Command], Ack]) -> None:
        """
        Internal method that runs the command listening loop in a separate thread.
        Makes sequential requests to the getCommand API, which now waits for commands
        to be available before returning.
        
        Args:
            on_command: Callback function that processes commands and returns acknowledgments
        """
        while self._running:
            # Poll for a command
            cmd = self._queue.poll()
            print(cmd)
            
            if cmd is not None:
                # Return command
                cmddecode = decode_command(cmd)
                ack = on_command(cmddecode)
            
            # Wait
            time.sleep(2)
    
    def activate_topic(self, topicid: str) -> None:
        """Activate a topic (no-op for now)."""
        pass

    def deactivate_topic(self, topicid: str) -> None:
        """Deactivate a topic (no-op for now)."""
        pass

    def publish_topic_data(self, topicid: str, data: Dict[str, Any]) -> None:
        """Publish data to a topic (no-op for now)."""
        pass
