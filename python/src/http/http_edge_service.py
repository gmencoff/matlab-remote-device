import time
import threading
import requests
from typing import Dict, Any, Callable, Optional
from src.services.edge_service import EdgeService
from src.commands.commands import Command, Ack, decode_command


class HttpEdgeService(EdgeService):
    """
    HTTP-based edge service that communicates with Firebase functions.
    Uses HTTP requests to publish config and receive commands from Firebase.
    """

    def __init__(self, device_id: str, poll_interval: float = 0.1):
        """
        Initialize the HTTP edge service.
        
        Args:
            device_id: Unique identifier for this device
            poll_interval: Interval in seconds for polling commands (default: 0.1s = 100ms)
        """
        self.device_id = device_id
        self.poll_interval = poll_interval
        self._running = False
        self._command_thread = None
        
        # Firebase function endpoints
        self.set_config_url = "https://setconfig-tgyovhjiqq-uc.a.run.app"
        self.get_command_url = "https://getcommand-tgyovhjiqq-uc.a.run.app"
        self.send_ack_url = "https://sendack-tgyovhjiqq-uc.a.run.app"

    def publish_config(self, config: Dict[str, Any]) -> None:
        """
        Publish the current configuration to Firebase using the setConfig function.
        
        Args:
            config: Configuration dictionary to publish
        """
        try:
            payload = {
                "deviceId": self.device_id,
                "config": config
            }
            
            response = requests.post(
                self.set_config_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Config published successfully for device {self.device_id}: {result.get('message', 'OK')}")
            else:
                error_msg = f"Failed to publish config. Status: {response.status_code}, Response: {response.text}"
                print(f"Error: {error_msg}")
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error while publishing config: {str(e)}"
            print(f"Error: {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error while publishing config: {str(e)}"
            print(f"Error: {error_msg}")
            raise Exception(error_msg)

    def subscribe_commands(self, on_command: Callable[[Command], Ack]) -> None:
        """
        Start polling for commands from Firebase using the getCommand function.
        When a command is received, it calls the on_command callback and sends the acknowledgment
        back via the sendAck function.
        
        Args:
            on_command: Callback function that processes commands and returns acknowledgments
        """
        if self._running:
            print("Command subscription is already running")
            return
            
        self._running = True
        self._command_thread = threading.Thread(target=self._command_polling_loop, args=(on_command,), daemon=True)
        self._command_thread.start()
        print(f"Started command polling for device {self.device_id}")

    def _command_polling_loop(self, on_command: Callable[[Command], Ack]) -> None:
        """
        Internal method that runs the command polling loop in a separate thread.
        
        Args:
            on_command: Callback function that processes commands and returns acknowledgments
        """
        while self._running:
            try:
                # Poll for commands
                response = requests.get(
                    self.get_command_url,
                    params={"deviceId": self.device_id},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    commands = data.get("commands", [])
                    
                    if commands:
                        print(f"Received {len(commands)} commands for device {self.device_id}")
                        
                        # Process each command
                        for command_data in commands:
                            try:
                                # Decode the command
                                command = decode_command(command_data.get("command", {}))
                                
                                # Process the command and get acknowledgment
                                ack = on_command(command)
                                
                                # Send acknowledgment back to Firebase
                                self._send_acknowledgment(command.id, ack)
                                
                            except Exception as e:
                                print(f"Error processing command {command_data.get('id', 'unknown')}: {str(e)}")
                                # Send error acknowledgment
                                error_ack = Ack(command_data.get('id', ''), False, "generic", str(e))
                                self._send_acknowledgment(command_data.get('id', ''), error_ack)
                
                elif response.status_code != 404:  # 404 is expected when no commands
                    print(f"Error polling commands. Status: {response.status_code}, Response: {response.text}")
                
            except requests.exceptions.RequestException as e:
                print(f"Network error while polling commands: {str(e)}")
            except Exception as e:
                print(f"Unexpected error in command polling loop: {str(e)}")
            
            # Wait before next poll
            time.sleep(self.poll_interval)

    def _send_acknowledgment(self, command_id: str, ack: Ack) -> None:
        """
        Send an acknowledgment back to Firebase using the sendAck function.
        
        Args:
            command_id: ID of the command being acknowledged
            ack: Acknowledgment object to send
        """
        try:
            payload = {
                "deviceId": self.device_id,
                "commandId": command_id,
                "response": ack.to_dict()
            }
            
            response = requests.post(
                self.send_ack_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Ack sent successfully for command {command_id}: {result.get('message', 'OK')}")
            else:
                print(f"Failed to send ack for command {command_id}. Status: {response.status_code}, Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Network error while sending ack for command {command_id}: {str(e)}")
        except Exception as e:
            print(f"Unexpected error while sending ack for command {command_id}: {str(e)}")

    def stop(self) -> None:
        """
        Stop the command polling loop.
        """
        if self._running:
            self._running = False
            if self._command_thread and self._command_thread.is_alive():
                self._command_thread.join(timeout=5)
            print(f"Stopped command polling for device {self.device_id}")

    def is_running(self) -> bool:
        """
        Check if the command polling is currently running.
        
        Returns:
            True if polling is active, False otherwise
        """
        return self._running
