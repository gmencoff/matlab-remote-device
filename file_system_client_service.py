import os, json, time, threading
from typing import Dict, Any, Callable
from interfaces import ClientService
from utils import read_json

class FileSystemClientService(ClientService):
    """
    File-system-based client service.
    Uses JSON files under a root directory to sync config and send commands.
    Intended for OneDrive/Dropbox/etc. synced folders.
    """

    def __init__(self, root: str, poll_s: float = 1.0):
        self.root = root
        self.config_path = os.path.join(root, "config", "config.json")
        self.commands_path = os.path.join(root, "commands", "commands.jsonl")
        self.acks_dir = os.path.join(root, "commands", "acks")
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        os.makedirs(self.acks_dir, exist_ok=True)
        self.poll_s = poll_s

    # ---- ClientService API ----

    def send_command(self, cmd: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
        """Append command to commands.jsonl, then wait for its ack in acks/<id>.json."""
        with open(self.commands_path, "a") as f:
            f.write(json.dumps(cmd) + "\n")

        ack_path = os.path.join(self.acks_dir, f"{cmd['id']}.json")
        deadline = time.time() + timeout
        while time.time() < deadline:
            if os.path.exists(ack_path):
                return read_json(ack_path)
            time.sleep(0.1)
        raise TimeoutError(f"No ack for {cmd['id']}")

    def subscribe_config(self, on_change: Callable[[Dict[str, Any]], None]) -> None:
        """Poll config.json and invoke callback whenever it changes."""
        def loop():
            last = None
            # Emit initial config if available
            if os.path.exists(self.config_path):
                cfg = read_json(self.config_path)
                on_change(cfg.copy())
                last = cfg
            while True:
                if os.path.exists(self.config_path):
                    cfg = read_json(self.config_path)
                    if cfg != last:
                        on_change(cfg.copy())
                        last = cfg
                time.sleep(self.poll_s)

        threading.Thread(target=loop, daemon=True).start()
