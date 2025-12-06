import json
import threading
import time
import websocket
from typing import Dict, Any, Callable, Optional
from src.services.edge_service import EdgeService
from src.commands.commands import Command, Ack, decode_command


class WsEdgeService(EdgeService):
    """
    WebSocket-based edge service that communicates with the WebSocket gateway server.
    Uses WebSocket connection to publish config and receive commands from the server.
    """

    def __init__(self, device_id: str, server_url: str = "ws://localhost:8080/ws"):
        """
        Initialize the WebSocket edge service and establish connection.
        
        Args:
            device_id: Unique identifier for this device
            server_url: WebSocket server URL (default: ws://localhost:8080/ws)
        """
        self.device_id = device_id
        self.server_url = server_url
        self._ws: Optional[websocket.WebSocketApp] = None
        self._running = True  # Connection should be running for object lifetime
        self._ws_thread: Optional[threading.Thread] = None
        self._on_command_callback: Optional[Callable[[Command], Ack]] = None
        self._connected = False
        self._connection_lock = threading.Lock()
        
        # Start WebSocket connection immediately
        self._ws_thread = threading.Thread(target=self._connect, daemon=True)
        self._ws_thread.start()
        
        # Wait a bit for connection to establish
        time.sleep(0.5)

    def _on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        """
        Handle incoming WebSocket messages.
        
        Args:
            ws: WebSocket connection
            message: Received message as string
        """
        try:
            data = json.loads(message)
            
            # Check if this is a command message from the server.
            # TODO: add a better way to parse messages from the server.
            if "commandId" in data and "command" in data:
                command_id = data.get("commandId")
                command_data = data.get("command", {})
                
                print(f"Received command for device {self.device_id}: {command_id}")
                
                try:
                    # Decode the command
                    command = decode_command(command_data)
                    
                    # Process the command if callback is registered
                    if self._on_command_callback:
                        ack = self._on_command_callback(command)
                        
                        # Send acknowledgment back to server
                        self._send_acknowledgment(command_id, ack)
                    else:
                        print(f"Warning: Received command but no callback registered")
                        # Send error acknowledgment
                        error_ack = Ack(command_id, False, "generic", "No command handler registered")
                        self._send_acknowledgment(command_id, error_ack)
                        
                except Exception as e:
                    print(f"Error processing command {command_id}: {str(e)}")
                    # Send error acknowledgment
                    error_ack = Ack(command_id, False, "generic", str(e))
                    self._send_acknowledgment(command_id, error_ack)
            else:
                print(f"Received unknown message type: {data}")
                
        except json.JSONDecodeError as e:
            print(f"Error decoding WebSocket message: {str(e)}")
        except Exception as e:
            print(f"Error handling WebSocket message: {str(e)}")

    def _on_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        """
        Handle WebSocket errors.
        
        Args:
            ws: WebSocket connection
            error: Error that occurred
        """
        print(f"WebSocket error for device {self.device_id}: {str(error)}")

    def _on_close(self, ws: websocket.WebSocketApp, close_status_code: int, close_msg: str) -> None:
        """
        Handle WebSocket connection close.
        
        Args:
            ws: WebSocket connection
            close_status_code: Close status code
            close_msg: Close message
        """
        print(f"WebSocket connection closed for device {self.device_id}: {close_status_code} - {close_msg}")
        with self._connection_lock:
            self._connected = False
        
        # Attempt to reconnect if still running
        if self._running:
            print(f"Attempting to reconnect for device {self.device_id}...")
            time.sleep(2)
            self._connect()

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        """
        Handle WebSocket connection open.
        
        Args:
            ws: WebSocket connection
        """
        print(f"WebSocket connection opened for device {self.device_id}")
        
        # Send hello message as the first message
        hello_message = {
            "type": "hello",
            "deviceId": self.device_id
        }
        ws.send(json.dumps(hello_message))
        
        with self._connection_lock:
            self._connected = True
        
        print(f"Sent hello message for device {self.device_id}")

    def _connect(self) -> None:
        """
        Establish WebSocket connection to the server.
        """
        try:
            self._ws = websocket.WebSocketApp(
                self.server_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            # Run forever in a separate thread
            self._ws.run_forever()
        except Exception as e:
            print(f"Error connecting WebSocket for device {self.device_id}: {str(e)}")
            with self._connection_lock:
                self._connected = False

    def _send_acknowledgment(self, command_id: str, ack: Ack) -> None:
        """
        Send an acknowledgment back to the server via WebSocket.
        
        Args:
            command_id: ID of the command being acknowledged
            ack: Acknowledgment object to send
        """
        if not self._ws or not self._connected:
            print(f"Warning: Cannot send ack for command {command_id} - WebSocket not connected")
            return
        
        try:
            ack_message = {
                "type": "ack",
                "deviceId": self.device_id,
                "commandId": command_id,
                "status": "ok" if ack.ok else "error",
                "response": ack.to_dict()
            }
            
            self._ws.send(json.dumps(ack_message))
            print(f"Ack sent successfully for command {command_id}")
            
        except Exception as e:
            print(f"Error sending ack for command {command_id}: {str(e)}")

    def publish_config(self, config: Dict[str, Any]) -> None:
        """
        Publish the current configuration to the server via WebSocket.
        
        Args:
            config: Configuration dictionary to publish
        """
        if not self._ws or not self._connected:
            raise Exception(f"Cannot publish config - WebSocket not connected for device {self.device_id}")
        
        try:
            config_message = {
                "type": "setConfig",
                "deviceId": self.device_id,
                "config": config
            }
            
            self._ws.send(json.dumps(config_message))
            print(f"Config published successfully for device {self.device_id}")
            
        except Exception as e:
            error_msg = f"Error publishing config via WebSocket: {str(e)}"
            print(f"Error: {error_msg}")
            raise Exception(error_msg)

    def subscribe_commands(self, on_command: Callable[[Command], Ack]) -> None:
        """
        Register a callback for incoming commands from the server via WebSocket.
        When a command is received, it calls the on_command callback 
        and sends the acknowledgment back via WebSocket.
        
        Args:
            on_command: Callback function that processes commands and returns acknowledgments
        """
        self._on_command_callback = on_command
        print(f"Registered command callback for device {self.device_id}")

    def activate_topic(self, topicid: str) -> None:
        """
        Activate a topic (no-op for now).
        
        Args:
            topicid: ID of the topic to activate
        """
        # No-op implementation
        pass

    def deactivate_topic(self, topicid: str) -> None:
        """
        Deactivate a topic (no-op for now).
        
        Args:
            topicid: ID of the topic to deactivate
        """
        # No-op implementation
        pass

    def publish_topic_data(self, topicid: str, data: Dict[str, Any]) -> None:
        """
        Publish data to a topic (no-op for now).
        
        Args:
            topicid: ID of the topic to publish data to
            data: Data to publish to the topic
        """
        # No-op implementation
        pass

    def stop(self) -> None:
        """
        Stop the WebSocket connection and command listening.
        """
        if self._running:
            self._running = False
            self._on_command_callback = None
            
            if self._ws:
                self._ws.close()
            
            if self._ws_thread and self._ws_thread.is_alive():
                self._ws_thread.join(timeout=5)
            
            print(f"Stopped WebSocket connection for device {self.device_id}")

    def __del__(self):
        """
        Cleanup when object is destroyed - close WebSocket connection.
        """
        self.stop()

    def is_running(self) -> bool:
        """
        Check if the WebSocket connection is currently running.
        
        Returns:
            True if connection is active, False otherwise
        """
        return self._running and self._connected

    def is_connected(self) -> bool:
        """
        Check if the WebSocket is currently connected.
        
        Returns:
            True if connected, False otherwise
        """
        with self._connection_lock:
            return self._connected
