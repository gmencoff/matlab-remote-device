import uuid
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.services.client_service import ClientService
from src.data.complex_number import ComplexNumberArray

class Ack:
    """Base class for command acknowledgments."""
    
    def __init__(self, command_id: str, ok: bool, ack_type: str, error: Optional[str] = None):
        self.id = command_id
        self.ok = ok
        self.type = ack_type
        self.error = error
        self.ts = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert acknowledgment to dictionary for serialization."""
        data = {
            "id": self.id,
            "ok": self.ok,
            "ts": self.ts,
            "type": self.type
        }
        if not self.ok and self.error:
            data["error"] = self.error
        return data

class PropertyAck(Ack):
    """Acknowledgment for property commands."""
    
    def __init__(self, command_id: str, ok: bool, value=None, error: Optional[str] = None):
        super().__init__(command_id, ok, ack_type="property", error=error)
        self.value = value
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        if self.ok and self.value is not None:
            data["value"] = self.value
        return data

class ReceiveAck(Ack):
    """Acknowledgment for receive commands containing I/Q samples."""
    
    def __init__(self, command_id: str, ok: bool, data: ComplexNumberArray = None, error: Optional[str] = None):
        super().__init__(command_id, ok, ack_type="receive", error=error)
        self.data = data
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        if self.ok and self.data is not None:
            data["data"] = self.data.to_dict()
        return data

class ReceiveStreamAck(Ack):
    """Acknowledgment for receive stream commands."""
    
    def __init__(self, command_id: str, ok: bool, error: Optional[str] = None):
        super().__init__(command_id, ok, ack_type="receive_stream", error=error)
    
    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict()

class Command(ABC):
    """Base class for all commands."""
    
    def __init__(self, type: str, id: str, ts: float):
        self.id = id
        self.type = type
        self.ts = ts
    
    @abstractmethod
    def execute(self, device: Any) -> Ack:
        """Execute this command on the given device and return an acknowledgment."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary for serialization."""
        return {
            "id": self.id,
            "ts": self.ts,
            "type": self.type
        }

class PropertySetController:
    """Controller for setting properties."""
    
    @abstractmethod
    def setPropCmd(self, name: str, value: Any, id: str, ts: float) -> PropertyAck:
        """Set a property on the device."""
        pass

class PropertyCommand(Command):
    """Command to set a property value."""
    
    def __init__(self, name: str, value: Any, id = None, ts = None):
        id = id or str(uuid.uuid4())
        ts = ts or time.time()
        super().__init__("property", id, ts)
        self.name = name
        self.value = value
    
    def execute(self, controller: PropertySetController) -> PropertyAck:
        """Execute the property set command on the device."""
        return controller.setPropCmd(self.name, self.value, self.id, self.ts)
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "name": self.name,
            "value": self.value
        })
        return data
    
    def send(self, client_service: ClientService, timeout = 5) -> PropertyAck:
        """Send the command using the provided client service."""
        resp = client_service.send_command(self.to_dict(), timeout=timeout)
        return PropertyAck(resp.get('id', self.id),resp.get('ok', False),resp.get('value'),error=resp.get('error'))

class ReceiveController:
    """Controller for setting properties."""
    
    @abstractmethod
    def rxCmd(self, id: str, ts: float) -> ReceiveAck:
        """Get receive samples from the device."""
        pass

class ReceiveCommand(Command):
    """Command to receive I/Q samples from the device."""
    
    def __init__(self, id = None, ts = None):
        id = id or str(uuid.uuid4())
        ts = ts or time.time()
        super().__init__("receive", id, ts)
    
    def execute(self, controller: ReceiveController) -> ReceiveAck:
        """Execute the receive command on the device."""
        return controller.rxCmd(self.id, self.ts)
    
    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict()
    
    def send(self, client_service: ClientService, timeout = 5) -> ReceiveAck:
        """Send the command using the provided client service."""
        resp = client_service.send_command(self.to_dict(), timeout=timeout)
        return ReceiveAck(
            resp.get('id', self.id),
            resp.get('ok', False),
            data=resp.get('data'),
            error=resp.get('error')
        )

class ReceiveStreamController:
    """Controller for setting properties."""
    
    @abstractmethod
    def rxStreamCmd(self, duration: float, cmdid: str) -> ReceiveStreamAck:
        """Stream receive samples from the device."""
        pass

class ReceiveStreamCommand(Command):
    """Command to receive I/Q samples from the device."""
    
    def __init__(self, duration: float, id = None, ts = None):
        id = id or str(uuid.uuid4())
        ts = ts or time.time()
        super().__init__("receive_stream", id, ts)
        self.duration = duration
    
    def execute(self, controller: ReceiveStreamController) -> ReceiveStreamAck:
        """Execute the receive command on the device."""
        return controller.rxStreamCmd(self.duration, self.id)
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "duration": self.duration
        })
        return data
    
    def send(self, client_service: ClientService, timeout = 5) -> ReceiveStreamAck:
        """Send the command using the provided client service."""
        resp = client_service.send_command(self.to_dict(), timeout=timeout)
        return ReceiveStreamAck(
            resp.get('id', self.id),
            resp.get('ok', False),
            error=resp.get('error')
        )

# Standalone decoder functions

def decode_command(data: Dict[str, Any]) -> Command:
    """Create a command instance from a dictionary."""
    if "type" not in data:
        raise ValueError("Command data missing 'type' field")
        
    command_type = data["type"]
    if command_type == "property":
        cmd = PropertyCommand(data["name"], data["value"], data["id"], data["ts"])
        return cmd
    elif command_type == "receive":
        cmd = ReceiveCommand(data["id"], data["ts"])
        return cmd
    elif command_type == "receive_stream":
        cmd = ReceiveStreamCommand(data["duration"], data["id"], data["ts"])
        return cmd
    else:
        raise ValueError(f"Unknown command type: {command_type}")


def decode_ack(data: Dict[str, Any]) -> Ack:
    """Create an acknowledgment instance from a dictionary."""
    ack_type = data.get("type", "generic")
    
    if ack_type == "property":
        return PropertyAck(
            data["id"], 
            data.get("ok", False),
            value=data.get("value"),
            error=data.get("error")
        )
    elif ack_type == "receive":
        return ReceiveAck(
            data["id"], 
            data.get("ok", False),
            data=data.get("data"),
            error=data.get("error")
        )
    elif ack_type == "receive_stream":
        return ReceiveStreamAck(
            data["id"], 
            data.get("ok", False),
            error=data.get("error")
        )
    else:  # generic or unknown type
        return Ack(
            data["id"], 
            data.get("ok", False),
            error=data.get("error")
        )
