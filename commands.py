from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from enum import Enum
import time, uuid

from interfaces import ClientService

class CommandType(str, Enum):
    PROPERTY = "property"
    METHOD = "method"

@dataclass
class Command:
    id: str
    type: CommandType
    name: str
    ts: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
@dataclass
class Ack:
    id: str
    ok: bool
    ts: float
    error: Optional[str] = None

@dataclass
class PropertyAck(Ack):
    value: Any = None

@dataclass
class PropertyCommand(Command):
    value: Any = None

    def __init__(self, name: str, value: Any):
        super().__init__(
            id=str(uuid.uuid4()),
            type=CommandType.PROPERTY,
            name=name,
            ts=time.time(),
        )
        self.value = value

    def send(self, client_service: ClientService) -> PropertyAck:
        raw = client_service.send_command(self.to_dict())
        return PropertyAck(**raw)

@dataclass
class MethodAck(Ack):
    result: Any = None

@dataclass
class MethodCommand(Command):
    args: List[Any] = None
    kwargs: Dict[str, Any] = None

    def __init__(self, name: str, args=None, kwargs=None):
        super().__init__(
            id=str(uuid.uuid4()),
            type=CommandType.METHOD,
            name=name,
            ts=time.time(),
        )
        self.args = args or []
        self.kwargs = kwargs or {}

    def send(self, client_service: ClientService) -> MethodAck:
        raw = client_service.send_command(self.to_dict())
        return MethodAck(**raw)
