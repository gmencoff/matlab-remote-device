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


class ReceiveAck(Ack):
    """Acknowledgment for receive commands containing I/Q samples."""
    
    def __init__(self, command_id: str, ok: bool, real_samples=None, imag_samples=None, error: Optional[str] = None):
        super().__init__(command_id, ok, ack_type="receive", error=error)
        self.real_samples = real_samples
        self.imag_samples = imag_samples
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        if self.ok and self.real_samples is not None and self.imag_samples is not None:
            data["real_samples"] = self.real_samples
            data["imag_samples"] = self.imag_samples
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

class PropertySetController:
    """Controller for setting properties."""
    
    @abstractmethod
    def setprop(self, name: str, value: Any):
        """Set a property on the device."""
        pass

    @abstractmethod
    def getprop(self, name: str) -> Any:
        """Get a property from the device."""
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
        
        try:
            # Set the property on the device
            controller.setprop(self.name, self.value)
            
            # Read back the actual value (might be different from requested)
            actual_value = controller.getprop(self.name)
            
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
    
    def send(self, client_service: ClientService, timeout = 5) -> PropertyAck:
        """Send the command using the provided client service."""
        resp = client_service.send_command(self.to_dict(), timeout=timeout)
        return PropertyAck(resp.get('id', self.id),resp.get('ok', False),resp.get('value'),error=resp.get('error'))

class ReceiveController:
    """Controller for setting properties."""
    
    @abstractmethod
    def rx(self) -> Any:
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
        try:
            
            # Get complex samples from device
            complex_samples = controller.rx()
            
            # Convert complex samples to real and imaginary parts
            if hasattr(complex_samples, 'real') and hasattr(complex_samples, 'imag'):
                # Handle numpy arrays or similar
                real_samples = complex_samples.real.tolist() if hasattr(complex_samples.real, 'tolist') else list(complex_samples.real)
                imag_samples = complex_samples.imag.tolist() if hasattr(complex_samples.imag, 'tolist') else list(complex_samples.imag)
            else:
                # Handle list of complex numbers
                real_samples = [sample.real for sample in complex_samples]
                imag_samples = [sample.imag for sample in complex_samples]
            
            return ReceiveAck(self.id, True, real_samples=real_samples, imag_samples=imag_samples)
            
        except Exception as e:
            return ReceiveAck(self.id, False, error=f"Error receiving samples: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        return super().to_dict()
    
    def send(self, client_service: ClientService, timeout = 5) -> ReceiveAck:
        """Send the command using the provided client service."""
        resp = client_service.send_command(self.to_dict(), timeout=timeout)
        return ReceiveAck(
            resp.get('id', self.id),
            resp.get('ok', False),
            real_samples=resp.get('real_samples'),
            imag_samples=resp.get('imag_samples'),
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
            real_samples=data.get("real_samples"),
            imag_samples=data.get("imag_samples"),
            error=data.get("error")
        )
    else:  # generic or unknown type
        return Ack(
            data["id"], 
            data.get("ok", False),
            error=data.get("error")
        )
