import os, json, time, threading
from typing import Dict, Any, Callable
from src.services.client_service import ClientService
from src.utils.utils import read_json
from src.filesystem.file_system_paths import FileSystemPaths

class FileSystemClientService(ClientService):
    """
    File-system-based client service.
    Uses JSON files under a root directory to sync config and send commands.
    Intended for OneDrive/Dropbox/etc. synced folders.
    """

    def __init__(self, root: str, poll_s: float = 1.0):
        self._paths = FileSystemPaths(root)
        self.poll_s = poll_s

    # ---- ClientService API ----

    def send_command(self, cmd: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
        """Append command to commands.jsonl, then wait for its ack in acks/<id>.json."""
        with open(self._paths.commands_path, "a") as f:
            f.write(json.dumps(cmd) + "\n")

        ack_path = self._paths.get_ack_path(cmd['id'])
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
            if os.path.exists(self._paths.config_path):
                cfg = read_json(self._paths.config_path)
                on_change(cfg.copy())
                last = cfg
            while True:
                if os.path.exists(self._paths.config_path):
                    cfg = read_json(self._paths.config_path)
                    if cfg != last:
                        on_change(cfg.copy())
                        last = cfg
                time.sleep(self.poll_s)

        threading.Thread(target=loop, daemon=True).start()
