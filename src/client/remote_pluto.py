import uuid, time
from typing import Any, Dict
from src.commands.commands import PropertyCommand
from src.services.client_service import ClientService

class RemotePluto:
    def __init__(self, client_service: ClientService):
        self._client_service = client_service
        self._state = []
        self._client_service.subscribe_config(self._on_config_update)

    def _on_config_update(self, cfg: Dict[str, Any]):
        self._state = cfg

    def __getattr__(self, name: str) -> Any:
        if name in self._state:
            return self._state[name]
        raise AttributeError(f"No such property: {name}")

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            return super().__setattr__(name, value)

        cmd = {
            "id": str(uuid.uuid4()),
            "type": "property",
            "name": name,
            "value": value,
            "ts": time.time()
        }
        cmd = PropertyCommand(name,value)
        ack = cmd.send(self._client_service)

        if ack.ok:
            # If we get an "ok", update the internal state. A remote config update could overwrite this.
            self._state[name] = ack.value
        else:
            raise RuntimeError(f"Failed to set {name}: {ack.error}")

    def call_method(self, name: str, *args, **kwargs) -> Dict[str, Any]:
        cmd = {
            "id": str(uuid.uuid4()),
            "type": "method",
            "name": name,
            "args": args,
            "kwargs": kwargs,
            "ts": time.time()
        }
        return self._client_service.send_command(cmd, timeout=5.0)
