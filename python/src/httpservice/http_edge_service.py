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

    def __init__(self, device_id: str):
        """
        Initialize the HTTP edge service.
        
        Args:
            device_id: Unique identifier for this device
        """
        self.device_id = device_id
        self._running = False
        self._command_thread = None
        
        # Firebase function endpoints
        self.set_config_url = "https://setconfig-tgyovhjiqq-uc.a.run.app"
        self.get_command_url = "https://getcommand-tgyovhjiqq-uc.a.run.app"
        self.send_ack_url = "https://sendack-tgyovhjiqq-uc.a.run.app"
        self.activate_topic_url = "https://activatetopic-tgyovhjiqq-uc.a.run.app"
        self.set_topic_data_url = "https://settopicdata-tgyovhjiqq-uc.a.run.app"

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
        Start listening for commands from Firebase using the getCommand function.
        The API now waits for commands to be available, so we make sequential requests
        instead of polling. When a command is received, it calls the on_command callback 
        and sends the acknowledgment back via the sendAck function.
        
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
            try:
                print(f"Waiting for commands for device {self.device_id}...")
                
                # Make request to getCommand API - this will wait until a command is available
                response = requests.get(
                    self.get_command_url,
                    params={"deviceId": self.device_id},
                    timeout=600  # 10 minute timeout to handle long waits
                )
                
                if response.status_code == 200:
                    data = response.json()
                    command_data = data.get("command")
                    
                    if command_data:
                        print(f"Received command for device {self.device_id}: {command_data.get('commandId', 'unknown')}")
                        
                        try:
                            # Decode the command
                            command = decode_command(command_data.get("command", {}))
                            
                            # Process the command and get acknowledgment
                            ack = on_command(command)
                            
                            # Send acknowledgment back to Firebase
                            self._send_acknowledgment(command.id, ack)
                            
                        except Exception as e:
                            print(f"Error processing command {command_data.get('commandId', 'unknown')}: {str(e)}")
                            # Send error acknowledgment
                            error_ack = Ack(command_data.get('commandId', ''), False, "generic", str(e))
                            self._send_acknowledgment(command_data.get('commandId', ''), error_ack)
                    else:
                        print(f"No command received for device {self.device_id}")
                
                elif response.status_code == 204:
                    # No command available (timeout reached)
                    print(f"No command available for device {self.device_id} within timeout period")
                
                elif response.status_code != 404:  # 404 is expected when no commands
                    print(f"Error getting commands. Status: {response.status_code}, Response: {response.text}")
                
            except requests.exceptions.Timeout:
                print(f"Request timeout for device {self.device_id} - no command available within timeout period")
            except requests.exceptions.RequestException as e:
                print(f"Network error while getting commands: {str(e)}")
                # Wait a bit before retrying on network errors
                if self._running:
                    time.sleep(5)
            except Exception as e:
                print(f"Unexpected error in command listening loop: {str(e)}")
                # Wait a bit before retrying on unexpected errors
                if self._running:
                    time.sleep(5)

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

    def activate_topic(self, topicid: str) -> None:
        """
        Activate a topic using the activateTopic Firebase function.
        
        Args:
            topicid: ID of the topic to activate
        """
        try:
            payload = {
                "deviceId": self.device_id,
                "topicId": topicid,
                "active": True
            }
            
            response = requests.post(
                self.activate_topic_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Topic {topicid} activated successfully for device {self.device_id}: {result.get('message', 'OK')}")
            else:
                error_msg = f"Failed to activate topic {topicid}. Status: {response.status_code}, Response: {response.text}"
                print(f"Error: {error_msg}")
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error while activating topic {topicid}: {str(e)}"
            print(f"Error: {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error while activating topic {topicid}: {str(e)}"
            print(f"Error: {error_msg}")
            raise Exception(error_msg)

    def deactivate_topic(self, topicid: str) -> None:
        """
        Deactivate a topic using the activateTopic Firebase function.
        
        Args:
            topicid: ID of the topic to deactivate
        """
        try:
            payload = {
                "deviceId": self.device_id,
                "topicId": topicid,
                "active": False
            }
            
            response = requests.post(
                self.activate_topic_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Topic {topicid} deactivated successfully for device {self.device_id}: {result.get('message', 'OK')}")
            else:
                error_msg = f"Failed to deactivate topic {topicid}. Status: {response.status_code}, Response: {response.text}"
                print(f"Error: {error_msg}")
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error while deactivating topic {topicid}: {str(e)}"
            print(f"Error: {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error while deactivating topic {topicid}: {str(e)}"
            print(f"Error: {error_msg}")
            raise Exception(error_msg)

    def publish_topic_data(self, topicid: str, data: Dict[str, Any]) -> None:
        """
        Publish data to a topic using the setTopicData Firebase function.
        
        Args:
            topicid: ID of the topic to publish data to
            data: Data to publish to the topic
        """
        try:
            payload = {
                "deviceId": self.device_id,
                "topicId": topicid,
                "data": data
            }
            
            response = requests.post(
                self.set_topic_data_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Data published successfully to topic {topicid} for device {self.device_id}: {result.get('message', 'OK')}")
            else:
                error_msg = f"Failed to publish data to topic {topicid}. Status: {response.status_code}, Response: {response.text}"
                print(f"Error: {error_msg}")
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error while publishing data to topic {topicid}: {str(e)}"
            print(f"Error: {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error while publishing data to topic {topicid}: {str(e)}"
            print(f"Error: {error_msg}")
            raise Exception(error_msg)

    def stop(self) -> None:
        """
        Stop the command listening loop.
        """
        if self._running:
            self._running = False
            if self._command_thread and self._command_thread.is_alive():
                self._command_thread.join(timeout=5)
            print(f"Stopped command listening for device {self.device_id}")

    def is_running(self) -> bool:
        """
        Check if the command listening is currently running.
        
        Returns:
            True if listening is active, False otherwise
        """
        return self._running
