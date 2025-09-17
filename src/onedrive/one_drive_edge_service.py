import subprocess
from typing import Dict, Any, Callable
from src.commands.commands import Command, Ack
from src.services.edge_service import EdgeService
from src.filesystem.file_system_edge_service import FileSystemEdgeService

class OneDriveEdgeService(EdgeService):
    """
    OneDrive edge service encapsulates the FileSystemEdgeService and calls
    some sync functions when required.
    """

    def __init__(self, local_folder: str, onedrive_folder: str, poll_s: float = 1.0):
        self._local_folder = local_folder
        self._onedrive_folder = onedrive_folder
        self._file_system_edge_service = FileSystemEdgeService(
            root=self._local_folder,
            poll_s=poll_s,
            pre_read_file_cb=self._pre_read_file_cb,
            post_write_file_cb=self._post_write_file_cb)
        
    # ---- EdgeService API ----

    def publish_config(self, config: Dict[str, Any]) -> None:
        self._file_system_edge_service.publish_config(config=config)

    def subscribe_commands(self, on_command: Callable[[Command], Ack]) -> None:
        self._file_system_edge_service.subscribe_commands(on_command=on_command)

    def _pre_read_file_cb(self, path: str):
        self._rclone_copy(self._onedrive_folder,self._local_folder,10)

    def _post_write_file_cb(self, path: str):
        self._rclone_copy(self._local_folder,self._onedrive_folder,10)

    def _rclone_copy(self,srcpath,destpath,timeout):
        cmd = ["rclone","copy",srcpath,destpath,"--progress=false","--stats=0"]

        try:
            subprocess.run(cmd,check=True,capture_output=True,text=True,timeout=timeout)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"rclone failed (exit {e.returncode}): {e.stderr.strip()}") from e
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"rclone timed out after {timeout}s")