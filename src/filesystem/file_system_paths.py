import os

class FileSystemPaths:
    """Shared configuration for file paths used by both client and edge services."""
    
    def __init__(self, root: str):
        self.root = root
        self.config_dir = os.path.join(root, "config")
        self.commands_dir = os.path.join(root, "commands")
        self.acks_dir = os.path.join(self.commands_dir, "acks")
        
        # Ensure directories exist
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.acks_dir, exist_ok=True)
        
        # Define file paths
        self.config_path = os.path.join(self.config_dir, "config.json")
        self.commands_path = os.path.join(self.commands_dir, "commands.jsonl")
    
    def get_ack_path(self, command_id: str) -> str:
        """Get the path for a specific command acknowledgment file."""
        return os.path.join(self.acks_dir, f"{command_id}.json")
