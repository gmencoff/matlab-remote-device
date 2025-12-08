import json
import asyncio
import threading
import time
import websockets
import ssl
from typing import Dict, Any, Callable, Optional
from src.services.edge_service import EdgeService
from src.commands.commands import Command, Ack, decode_command


class WsEdgeService(EdgeService):
    """
    WebSocket-based edge service that communicates with the WebSocket gateway server.
    Uses WebSocket connection to publish config and receive commands from the server.
    """

    def __init__(self, device_id: str, server_url: str = "ws://localhost:8080/ws", ssl_verify: bool = True):
        """
        Initialize the WebSocket edge service and establish connection.
        
        Args:
            device_id: Unique identifier for this device
            server_url: WebSocket server URL (default: ws://localhost:8080/ws)
            ssl_verify: Whether to verify SSL certificates for wss:// connections (default: True)
        """
        self.device_id = device_id
        self.server_url = server_url
        self._ssl_verify = ssl_verify
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._running = True
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._on_command_callback: Optional[Callable[[Command], Ack]] = None
        self._connected = False
        self._connection_lock = threading.Lock()
        self._current_config = {}
        
        # Start async event loop in background thread
        self._loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._loop_thread.start()
        
        # Wait a bit for connection to establish
        time.sleep(0.5)

    def _run_event_loop(self) -> None:
        """Run the async event loop in a background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect())

    async def _connect(self) -> None:
        """Establish WebSocket connection to the server using async with syntax."""
        while self._running:
            try:
                # Determine if this is a secure (wss://) connection
                is_secure = self.server_url.startswith("wss://")
                
                # Prepare SSL context
                ssl_context = None
                if is_secure:
                    if self._ssl_verify:
                        ssl_context = ssl.create_default_context()
                    else:
                        # Disable certificate verification for development/testing
                        ssl_context = ssl.create_default_context()
                        ssl_context.check_hostname = False
                        ssl_context.verify_mode = ssl.CERT_NONE

                # Use async with websockets.connect() syntax
                async with websockets.connect(
                    self.server_url,
                    ssl=ssl_context
                ) as websocket:
                    self._ws = websocket
                    
                    print(f"WebSocket connection opened for device {self.device_id}")
                    
                    # Send hello message as the first message
                    hello_message = {
                        "type": "hello",
                        "deviceId": self.device_id,
                        "config": self._current_config
                    }
                    await websocket.send(json.dumps(hello_message))
                    
                    with self._connection_lock:
                        self._connected = True
                    
                    print(f"Sent hello message for device {self.device_id}")
                    
                    # Listen for messages
                    async for message in websocket:
                        if not self._running:
                            break
                        await self._handle_message(message)
                        
            except websockets.exceptions.ConnectionClosed:
                print(f"WebSocket connection closed for device {self.device_id}")
                with self._connection_lock:
                    self._connected = False
                    self._ws = None
                
                if self._running:
                    print(f"Attempting to reconnect for device {self.device_id}...")
                    await asyncio.sleep(2)
                    
            except Exception as e:
                print(f"Error connecting WebSocket for device {self.device_id}: {str(e)}")
                with self._connection_lock:
                    self._connected = False
                    self._ws = None
                
                if self._running:
                    print(f"Attempting to reconnect for device {self.device_id}...")
                    await asyncio.sleep(2)

    async def _handle_message(self, message: str) -> None:
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            
            # Check if this is a command message from the server
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
                        await self._send_acknowledgment(command_id, ack)
                    else:
                        print(f"Warning: Received command but no callback registered")
                        error_ack = Ack(command_id, False, "generic", "No command handler registered")
                        await self._send_acknowledgment(command_id, error_ack)
                        
                except Exception as e:
                    print(f"Error processing command {command_id}: {str(e)}")
                    error_ack = Ack(command_id, False, "generic", str(e))
                    await self._send_acknowledgment(command_id, error_ack)
            else:
                print(f"Received unknown message type: {data}")
                
        except json.JSONDecodeError as e:
            print(f"Error decoding WebSocket message: {str(e)}")
        except Exception as e:
            print(f"Error handling WebSocket message: {str(e)}")

    async def _send_acknowledgment(self, command_id: str, ack: Ack) -> None:
        """Send an acknowledgment back to the server via WebSocket."""
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
            
            await self._ws.send(json.dumps(ack_message))
            print(f"Ack sent successfully for command {command_id}")
            
        except Exception as e:
            print(f"Error sending ack for command {command_id}: {str(e)}")

    def publish_config(self, config: Dict[str, Any]) -> None:
        """Publish the current configuration to the server via WebSocket."""
        self._current_config = config
        if not self._ws or not self._connected or not self._loop:
            raise Exception(f"Cannot publish config - WebSocket not connected for device {self.device_id}")
        
        try:
            config_message = {
                "type": "setConfig",
                "deviceId": self.device_id,
                "config": config
            }
            
            # Schedule the send in the event loop
            asyncio.run_coroutine_threadsafe(
                self._ws.send(json.dumps(config_message)),
                self._loop
            ).result(timeout=5)
            
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
        """Activate a topic (no-op for now)."""
        pass

    def deactivate_topic(self, topicid: str) -> None:
        """Deactivate a topic (no-op for now)."""
        pass

    def publish_topic_data(self, topicid: str, data: Dict[str, Any]) -> None:
        """Publish data to a topic (no-op for now)."""
        pass

    def stop(self) -> None:
        """Stop the WebSocket connection and command listening."""
        if self._running:
            self._running = False
            self._on_command_callback = None
            
            if self._loop:
                # Schedule close in the event loop
                if self._ws:
                    asyncio.run_coroutine_threadsafe(
                        self._ws.close(),
                        self._loop
                    )
                # Stop the event loop
                self._loop.call_soon_threadsafe(self._loop.stop)
            
            if self._loop_thread and self._loop_thread.is_alive():
                self._loop_thread.join(timeout=5)
            
            print(f"Stopped WebSocket connection for device {self.device_id}")

    def __del__(self):
        """Cleanup when object is destroyed - close WebSocket connection."""
        self.stop()

    def is_running(self) -> bool:
        """Check if the WebSocket connection is currently running."""
        return self._running and self._connected

    def is_connected(self) -> bool:
        """Check if the WebSocket is currently connected."""
        with self._connection_lock:
            return self._connected
