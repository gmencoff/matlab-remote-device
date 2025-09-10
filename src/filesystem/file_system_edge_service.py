import os
import json
import time
import threading
from typing import Dict, Any, Callable
from src.services.edge_service import EdgeService
from src.commands.commands import Command, Ack, decode_command
from src.filesystem.file_system_paths import FileSystemPaths
from src.utils.utils import read_json

class FileSystemEdgeService(EdgeService):
    """
    File-system-based edge service.
    Uses JSON files under a root directory to publish config and receive commands.
    Counterpart to FileSystemClientService.
    """

    def __init__(self, root: str, poll_s: float = 1.0):
        self.paths = FileSystemPaths(root)
        self.poll_s = poll_s
        self._last_command_position = 0
        
        # Create empty commands file if it doesn't exist
        if not os.path.exists(self.paths.commands_path):
            with open(self.paths.commands_path, "w") as f:
                pass

    # ---- EdgeService API ----

    def publish_config(self, config: Dict[str, Any]) -> None:
        """Write the current configuration to config.json."""
        # Write to a temporary file first, then rename to avoid partial reads
        temp_path = f"{self.paths.config_path}.tmp"
        with open(temp_path, "w") as f:
            json.dump(config, f, indent=2)

        # Retry logic with exponential backoff
        max_attempts = 5
        base_delay = 0.1  # seconds
        
        for attempt in range(max_attempts):
            try:
                os.replace(temp_path, self.paths.config_path)
                return  # Success
            except OSError as e:
                if attempt == max_attempts - 1:
                    raise  # Re-raise on last attempt
                
                # Exponential backoff
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)

    def subscribe_commands(self, on_command: Callable[[Command], Ack]) -> None:
        """Poll commands.jsonl for new commands and invoke callback for each."""
        def loop():
            while True:
                try:
                    # Check if commands file exists and has content
                    if os.path.exists(self.paths.commands_path) and os.path.getsize(self.paths.commands_path) > 0:
                        with open(self.paths.commands_path, "r") as f:
                            
                            # Seek to last read position
                            f.seek(self._last_command_position)
                            
                            # Read new commands
                            new_commands = f.readlines()
                            
                            # Update position for next read
                            self._last_command_position = f.tell()
                            
                            # Process each new command
                            for cmd_line in new_commands:
                                if cmd_line.strip():  # Skip empty lines
                                    try:
                                        cmd_dict = json.loads(cmd_line)
                                        cmd = decode_command(cmd_dict)
                                        
                                        # Process command and get acknowledgment
                                        ack = on_command(cmd)
                                        
                                        # Write acknowledgment to file
                                        ack_path = self.paths.get_ack_path(cmd.id)
                                        with open(ack_path, "w") as ack_file:
                                            json.dump(ack.to_dict(), ack_file, indent=2)
                                    except json.JSONDecodeError:
                                        print(f"Invalid JSON in command: {cmd_line}")
                                    except Exception as e:
                                        print(f"Error processing command: {e}")
                except Exception as e:
                    print(f"Error in command subscription loop: {e}")
                
                time.sleep(self.poll_s)

        threading.Thread(target=loop, daemon=True).start()
