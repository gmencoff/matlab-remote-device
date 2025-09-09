import uuid
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.services.client_service import ClientService

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


class MethodAck(Ack):
    """Acknowledgment for method commands."""
    
    def __init__(self, command_id: str, ok: bool, result=None, error: Optional[str] = None):
        super().__init__(command_id, ok, ack_type="method", error=error)
        self.result = result
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        if self.ok and self.result is not None:
            data["result"] = self.result
        return data


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


class PropertyCommand(Command):
    """Command to set a property value."""
    
    def __init__(self, name: str, value: Any, id = None, ts = None):
        id = id or str(uuid.uuid4())
        ts = ts or time.time()
        super().__init__("property", id, ts)
        self.name = name
        self.value = value
    
    def execute(self, device: Any) -> PropertyAck:
        """Execute the property set command on the device."""
        try:
            # Set the property on the device
            setattr(device, self.name, self.value)
            
            # Read back the actual value (might be different from requested)
            actual_value = getattr(device, self.name)
            
            return PropertyAck(self.id, True, value=actual_value)
        except AttributeError:
            return PropertyAck(self.id, False, error=f"Property not found: {self.name}")
        except Exception as e:
            return PropertyAck(self.id, False, error=f"Error setting {self.name}: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "name": self.name,
            "value": self.value
        })
        return data
    
    def send(self, client_service: ClientService) -> PropertyAck:
        """Send the command using the provided client service."""
        resp = client_service.send_command(self.to_dict())
        return PropertyAck(resp.get('id', self.id),resp.get('ok', False),resp.get('value'),error=resp.get('error'))

class MethodCommand(Command):
    """Command to call a method."""
    
    def __init__(self, name: str, args=None, kwargs=None, id = None, ts = None):
        id = id or str(uuid.uuid4())
        ts = ts or time.time()
        super().__init__("method", id, ts)
        self.name = name
        self.args = args or []
        self.kwargs = kwargs or {}
    
    def execute(self, device: Any) -> MethodAck:
        """Execute the method call command on the device."""
        try:
            # Get the method from the device
            method = getattr(device, self.name)
            
            # Call the method
            result = method(*self.args, **self.kwargs)
            
            return MethodAck(self.id, True, result=result)
        except AttributeError:
            return MethodAck(self.id, False, error=f"Method not found: {self.name}")
        except Exception as e:
            return MethodAck(self.id, False, error=f"Error calling {self.name}: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "name": self.name,
            "args": self.args,
            "kwargs": self.kwargs
        })
        return data
    
    def send(self, client_service: ClientService) -> MethodAck:
        """Send the command using the provided client service."""
        resp = client_service.send_command(self.to_dict())
        return MethodAck(resp.get('id', self.id),resp.get('ok', False),resp.get('result'),resp.get('error'))


# Standalone decoder functions

def decode_command(data: Dict[str, Any]) -> Command:
    """Create a command instance from a dictionary."""
    if "type" not in data:
        raise ValueError("Command data missing 'type' field")
        
    command_type = data["type"]
    if command_type == "property":
        cmd = PropertyCommand(data["name"], data["value"], data["id"], data["ts"])
        return cmd
    elif command_type == "method":
        cmd = MethodCommand(data["name"], data.get("args", []), data.get("kwargs", {}), data["id"], data["ts"])
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
    elif ack_type == "method":
        return MethodAck(
            data["id"], 
            data.get("ok", False),
            result=data.get("result"),
            error=data.get("error")
        )
    else:  # generic or unknown type
        return Ack(
            data["id"], 
            data.get("ok", False),
            error=data.get("error")
        )
