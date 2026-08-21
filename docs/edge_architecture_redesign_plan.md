# Edge Architecture Redesign — Initial Implementation Plan

## Goal

Replace the prototype edge architecture with a generic, self-describing device framework. This phase covers **only the edge implementation and its control-plane communication with the existing server application**.

Out of scope for this phase:

- MATLAB / remote-client implementation
- High-throughput data streaming
- Real Pluto or other hardware-device implementations
- Backward compatibility with the prototype APIs

The target architecture is:

```text
FakeEdgeDevice : EdgeDevice
          |
          v
EdgeDeviceController
          |
          v
EdgeService
          |
          v
WebSocketEdgeService
          |
          v
Server
```

The existing prototype should be treated as reference material only. Breaking changes are acceptable.

---

## 1. Package Structure

Create the new edge implementation approximately as:

```text
python/
    src/
        edge/
            __init__.py
            device.py
            decorators.py
            descriptions.py
            protocol.py
            events.py
            controller.py

            services/
                __init__.py
                edge_service.py
                websocket_edge_service.py

    tests/
        edge/
            test_decorators.py
            test_device.py
            test_controller.py
            test_protocol.py
            test_edge_service.py
            test_websocket_edge_service.py
            test_integration.py
```

The implementer may adjust paths to fit the repository's existing import/package conventions, but the separation of responsibilities should remain.

---

## 2. In-Process `Event`

Implement a lightweight reusable observer class:

```python
event.subscribe(callback)
event.unsubscribe(callback)
event.emit(...)
```

Requirements:

- Callbacks execute synchronously and deterministically.
- A subscriber exception must **not propagate through `emit()`**.
- Subscriber failures should be logged and other subscribers should still be notified.
- This event mechanism is strictly in-process and should remain distinct from network events or distributed pub/sub.

---

## 3. `remote_property`

Implement a property-compatible decorator:

```python
@remote_property()
def gain(self) -> float:
    ...
```

Dynamic visibility is supported through:

```python
@remote_property(
    visible_if=lambda self: self.mode == "rx"
)
def rx_gain(self) -> float:
    ...
```

### V1 semantics

`remote_property` supports only one explicit option:

```python
visible_if
```

which defaults to always visible.

The decorator must:

- Behave like a normal Python property.
- Preserve its remote metadata through `.setter()`.
- Infer readability from the getter.
- Infer writability from whether a setter exists.
- Infer the remote type from the getter return annotation.
- Automatically emit:

```python
obj.property_changed.emit(property_name)
```

after a successful setter call.
- Emit no property-change event if the setter raises.

Ordinary `@property` members must never be remotely exposed.

Do not support write-only remote properties in v1.

Do not implement a validation framework in v1. Device setters and underlying hardware APIs remain authoritative for value validation.

A likely future extension is a composable `validation=` abstraction rather than adding individual `min`, `max`, `allowed_values`, etc. parameters to the decorator.

---

## 4. `remote_method`

Implement:

```python
@remote_method()
def calibrate(self, channel: int = 0) -> bool:
    ...
```

with optional dynamic visibility:

```python
@remote_method(
    visible_if=lambda self: self.mode == "rx"
)
def capture(...):
    ...
```

The framework must infer using `inspect.signature()` and annotations:

- Method name
- Argument names
- Argument types
- Required versus optional arguments
- Default values
- Return type

V1 supports:

- Positional arguments
- Keyword arguments
- Ordinary default arguments

V1 does **not** support:

- `*args`
- `**kwargs`
- Runtime framework type validation

Remote method names must equal their Python method names.

---

## 5. Type System

For properties and method inputs/outputs, support:

```text
bool
int
float
str
list[bool]
list[int]
list[float]
list[str]
```

Methods may additionally return:

```text
None
```

Rules:

- Annotations define the remote contract.
- Do not infer types from runtime values.
- Remote properties must have supported getter return annotations.
- Remote method inputs must have supported annotations.
- Remote methods must have a supported return annotation.
- Missing or unsupported required annotations must cause description generation to fail with a clear framework error.
- Do not support NumPy arrays or arbitrary Python objects in this control-plane type system in v1.

---

## 6. `EdgeDevice`

Implement a concrete `EdgeDevice` base class.

Because it owns event state, it must have an initializer:

```python
class EdgeDevice:
    def __init__(self):
        self.property_changed = Event()
        self.description_changed = Event()
```

Subclasses that define their own `__init__()` must call:

```python
super().__init__()
```

### Public API

Provide:

```python
describe()
get_state()
get_property(name)
set_property(name, value)
call_method(name, *args, **kwargs)
```

Also provide internal helpers for introspection of:

- Declared remote properties
- Active remote properties
- Declared remote methods
- Active remote methods

### Exposure rules

Only members decorated with:

```python
@remote_property
@remote_method
```

are remotely exposed.

`visible_if(self)` determines whether a member is currently active.

If `visible_if` raises, propagate the exception.

An inactive member behaves remotely as though it does not exist.

### Operation behavior

`get_property()`:

- Verify the property exists remotely.
- Verify it is currently visible.
- Invoke the actual property getter.

`set_property()`:

- Verify the property exists remotely.
- Verify it is currently visible.
- Verify it is writable.
- Invoke the actual property setter.
- Let setter/device exceptions propagate.

`call_method()`:

- Verify the method exists remotely.
- Verify it is currently visible.
- Invoke the ordinary Python method.
- Let method/device exceptions propagate.

Protocol/error conversion does not belong in `EdgeDevice`; it belongs in `EdgeDeviceController`.

---

## 7. Interface, State, and Snapshot Dataclasses

Separate the device interface from its current state.

### Interface descriptions

```python
@dataclass
class PropertyDescription:
    name: str
    type: str
    writable: bool
```

```python
@dataclass
class ArgumentDescription:
    name: str
    type: str
    required: bool
    default: Any
```

```python
@dataclass
class MethodDescription:
    name: str
    inputs: list[ArgumentDescription]
    return_type: str
```

```python
@dataclass
class DeviceDescription:
    properties: list[PropertyDescription]
    methods: list[MethodDescription]
```

### Device state

```python
@dataclass
class PropertyState:
    name: str
    value: Any
```

```python
@dataclass
class DeviceState:
    properties: list[PropertyState]
```

Use a list rather than a dictionary to keep serialization deterministic and each property's name/value bundled together.

### Full synchronization

```python
@dataclass
class DeviceSnapshot:
    description: DeviceDescription
    state: DeviceState
```

### Semantics

`describe()` returns only the active interface metadata.

`get_state()` reads every active remote property's getter exactly once and returns `DeviceState`.

If any getter fails, `get_state()` fails rather than returning partial state.

Do not cache descriptions or state in v1.

---

## 8. Device Events and State Synchronization

There are two in-process device notifications.

### Property value changes

Assignments through `remote_property` setters automatically emit:

```python
property_changed.emit(property_name)
```

If the underlying hardware changes independently of the `EdgeDevice` wrapper, the concrete device implementation is responsible for detecting it and emitting:

```python
property_changed.emit(property_name)
```

Preferred detection order:

1. Hardware/library callback or event
2. Device-specific polling only when necessary

Do not implement generic polling in `EdgeDevice`.

### Interface/capability changes

If a change affects which remote properties or methods are visible, the concrete device implementation must explicitly emit:

```python
description_changed.emit()
```

This is an intentional responsibility for device authors.

Do not implement automatic dependency scanning or comparison-based description-change detection.

If one operation changes both a property value and the interface, both events may be emitted. Accept the redundancy in v1.

---

## 9. Generic Protocol Dataclasses

Use typed dataclasses between `EdgeService` and `EdgeDeviceController`.

### Requests

```python
@dataclass
class Request:
    request_id: str
```

```python
@dataclass
class DescribeRequest(Request):
    pass
```

```python
@dataclass
class GetRequest(Request):
    property_name: str
```

```python
@dataclass
class SetRequest(Request):
    property_name: str
    value: Any
```

```python
@dataclass
class CallRequest(Request):
    method_name: str
    args: list[Any]
    kwargs: dict[str, Any]
```

`request_id` is a request/correlation identifier only. It is **not** the device ID.

### Responses

Use one generic response:

```python
@dataclass
class Response:
    request_id: str
    success: bool
    result: Any = None
    error: Error | None = None
```

Semantics:

- `describe` -> return a `DeviceSnapshot`
- `get` -> return the current property value
- `set` -> return the **actual property value read back after setting**
- `call` -> return the method result

Do not include timestamps in v1.

---

## 10. Error Model

Use:

```python
@dataclass
class Error:
    code: str
    message: str
```

Define stable error codes at least for:

```text
PROPERTY_NOT_FOUND
PROPERTY_NOT_WRITABLE
METHOD_NOT_FOUND
INVALID_ARGUMENTS
DEVICE_ERROR
INTERNAL_ERROR
```

Rules:

- Do not expose Python exception classes remotely.
- Do not expose tracebacks remotely.
- Do not expose implementation internals remotely.
- Known framework failures map to specific stable error codes.
- Property getter/setter and remote-method exceptions map to `DEVICE_ERROR`.
- Preserve a useful human-readable `str(exception)` as the error message.
- Unexpected framework/controller exceptions map to `INTERNAL_ERROR`.
- Log the original exception and traceback on the edge for debugging.

---

## 11. Network Events

Define typed network events.

V1 requires only:

```python
@dataclass
class PropertyChangedEvent:
    name: str
    value: Any
```

and:

```python
@dataclass
class DeviceSnapshotEvent:
    snapshot: DeviceSnapshot
```

Do **not** implement `DescriptionChangedEvent` in v1.

### Publication rules

```text
Ordinary property value change
    -> PropertyChangedEvent

Interface/capability change
    -> DeviceSnapshotEvent

Service connection/reconnection
    -> DeviceSnapshotEvent
```

A `DeviceSnapshot` is the authoritative full synchronization primitive.

The server can maintain canonical state by applying `PropertyChangedEvent` deltas between snapshots.

---

## 12. `EdgeDeviceController`

Implement one generic controller:

```python
controller = EdgeDeviceController(device, service)
```

It owns/references exactly one `EdgeDevice` and one `EdgeService`.

Construction must perform no network I/O.

### Lifecycle

```python
controller.start()
controller.stop()
```

### Responsibilities

The controller must:

- Register the request handler with `EdgeService`.
- Subscribe to `device.property_changed`.
- Subscribe to `device.description_changed`.
- Subscribe to `service.connected`.
- Dispatch `DescribeRequest`.
- Dispatch `GetRequest`.
- Dispatch `SetRequest`.
- Dispatch `CallRequest`.
- Produce generic `Response` objects.
- Catch and translate errors according to the error model.
- Serialize remote operations against the device.
- Translate device events into network events.

### Property-change handling

When:

```python
device.property_changed.emit(name)
```

fires:

```text
read device.get_property(name)
    ->
PropertyChangedEvent(name, actual_value)
    ->
service.publish_event(...)
```

The controller must **not** emit an additional property event merely because it processed `SetRequest`; the `remote_property` setter is already the event source.

### Description-change handling

When:

```python
device.description_changed.emit()
```

fires:

```text
device.describe()
+
device.get_state()
    ->
DeviceSnapshot
    ->
DeviceSnapshotEvent
    ->
service.publish_event(...)
```

### Connection handling

When:

```python
service.connected.emit()
```

fires, publish a fresh full `DeviceSnapshotEvent`.

---

## 13. Concurrency

Only one remote request may execute against a given `EdgeDevice` at a time.

Requests from multiple remote clients must therefore be serialized through the controller/service execution path.

Do not support parallel device calls in v1.

Hardware-originated events may come from background threads, so event publication must be safe to invoke from them.

---

## 14. `EdgeService`

Define the abstract control-plane transport approximately as:

```python
class EdgeService(ABC):
    connected: Event

    def start(self, request_handler): ...
    def send_response(self, response: Response): ...
    def publish_event(self, event): ...
    def stop(self): ...
```

### Responsibilities

`EdgeService` should transport typed Python protocol objects.

Concrete services own:

- Wire serialization/deserialization
- Network connections
- Reconnection behavior
- Server interaction
- Device registration/routing details

### Lifecycle

Construction performs no I/O.

`start(request_handler)`:

- Establishes/begins the connection.
- Starts request processing.
- Calling `start()` twice is an error.

`stop()`:

- Stops processing.
- Closes network resources.
- Is idempotent.

Every successful initial connection or reconnection must emit:

```python
connected.emit()
```

The controller responds by publishing a fresh `DeviceSnapshotEvent`.

---

## 15. Device Identity

`device_id` belongs to `EdgeService`, not `EdgeDevice`.

Example:

```python
WebSocketEdgeService(
    device_id="workstation-07-radio",
    server_url=...
)
```

Rules:

- `EdgeDevice` contains no device identity fields.
- `EdgeDeviceController` handles exactly one already-selected device.
- Controller-facing request dataclasses do not contain `device_id`.
- The concrete service uses `device_id` for server registration and routing.
- Events and responses are associated with the service's device ID when serialized.

---

## 16. WebSocket Transport and Server Changes

Implement only:

```text
WebSocketEdgeService
```

in this phase.

Do not preserve the old Firebase/HTTP implementation.

Update the existing server application as needed to support the new protocol. Backward compatibility is not required.

The server should be designed so edge events can eventually fan out to multiple remote clients connected to the same device.

The edge implementation itself must remain unaware of how many remote clients exist.

---

## 17. Wire Format

Use JSON with an explicit top-level protocol version.

Example:

```json
{
  "protocol_version": 1,
  "device_id": "workstation-07-radio",
  "request": {
    "request_id": "abc123",
    "type": "set",
    "property_name": "gain",
    "value": 10
  }
}
```

Keep protocol versioning at the transport-envelope level rather than adding versions to every dataclass.

`WebSocketEdgeService` is responsible for converting:

```text
JSON <-> typed protocol dataclasses
```

---

## 18. Fake Device

Do not implement a Pluto device in this phase.

Create a reusable `FakeEdgeDevice` for tests that exercises:

- Writable remote property
- Read-only remote property
- Scalar property types
- Homogeneous list property types
- Ordinary remote method
- Remote method with optional/default argument
- Dynamic `visible_if`
- Configuration change that changes visible members
- Setter failure
- Method failure
- Explicit externally generated property change
- Explicit description change

The fake device is the reference implementation for the framework contract.

---

## 19. Testing

Use `pytest`.

### Decorator tests

Cover:

- `remote_property` behavior
- Metadata preservation through `.setter()`
- Automatic `property_changed` emission
- No event on failed setter
- `visible_if`
- `remote_method`
- Signature/annotation inspection

### `EdgeDevice` tests

Cover:

- Description generation
- State generation
- Get/set/call
- Visibility rules
- Read-only handling
- Unsupported/missing types
- Property-change events
- Description-change events
- Device exceptions

### `EdgeDeviceController` tests

Cover:

- Request dispatch
- Generic responses
- Error conversion
- Property change -> `PropertyChangedEvent`
- Description change -> `DeviceSnapshotEvent`
- Service connection -> `DeviceSnapshotEvent`
- Serialized device execution
- Multiple simulated callers

### `EdgeService` contract tests

Use a fake service and verify:

- Lifecycle
- Handler registration
- Response sending
- Event publication
- Connected event

### WebSocket service tests

Cover:

- JSON serialization
- JSON deserialization
- Protocol version
- Connection lifecycle
- Reconnect behavior where practical without a deployed external server

### Integration tests

Use:

```text
FakeEdgeDevice
    +
FakeEdgeService
    +
EdgeDeviceController
```

Verify at least:

- Initial connection publishes a full snapshot.
- Reconnect publishes a fresh snapshot.
- Remote get succeeds.
- Remote set returns actual read-back value.
- Successful set publishes a property-change event.
- Two simulated clients changing the same device are serialized.
- External property change publishes a property event.
- Visibility-changing setter may produce both property event and full snapshot.
- Read-only set fails correctly.
- Invalid property/method fails correctly.
- Device exception becomes `DEVICE_ERROR`.
- Subscriber exception does not make a successful device mutation appear to fail.
- Invisible properties/methods behave as nonexistent.
- Unsupported/missing annotations fail description generation.

Normal tests must not require:

- Real hardware
- MATLAB
- Deployment credentials
- Server secrets
- External network dependencies
- A deployed production server

---

## 20. GitHub Actions CI

Add `pytest` to the Python development/test dependencies.

Add a workflow such as:

```text
.github/workflows/python-tests.yml
```

Trigger it on:

```yaml
on:
  push:
  pull_request:
```

`pull_request` is GitHub's equivalent of a merge-request workflow.

### Workflow steps

1. Check out the repository.
2. Install a supported Python version.
3. Install runtime and test dependencies.
4. Run the full Python test suite with `pytest`.
5. Fail the workflow on any test failure.

Use Linux initially unless a future implementation requirement demands another OS.

The workflow must not require:

- Hardware
- MATLAB
- Deployment credentials
- Server secrets
- External services

A pull request should therefore be verifiable using deterministic local/unit/integration tests alone.

---

## 21. Cleanup

Backward compatibility with the existing prototype is not required.

Once the new edge path is operational:

- Remove or clearly supersede obsolete edge-only prototype code.
- Do not retain special-purpose command classes such as receive/receive-stream merely for compatibility.
- Do not maintain both the old and new edge architectures in parallel unless temporarily required during implementation.
- Do not remove unrelated MATLAB/client prototype code unless necessary; the remote redesign is a separate phase.

---

## Acceptance Criteria

This phase is complete when a fake edge device can:

1. Start through:

```text
EdgeDeviceController
    +
WebSocketEdgeService
```

2. Advertise its dynamic interface and current state through a full `DeviceSnapshot`.
3. Service generic:
   - `describe`
   - `get`
   - `set`
   - `call`
4. Return the actual read-back value from successful sets.
5. Broadcast property-value deltas through `PropertyChangedEvent`.
6. Broadcast authoritative full snapshots when its interface changes.
7. Publish a fresh snapshot after connection or reconnection.
8. Correctly synchronize multiple remote callers through serialized device access.
9. Convert device/framework errors into stable protocol errors.
10. Recover state consistency through snapshot resynchronization.
11. Pass the complete Python test suite locally.
12. Run and pass the same test suite automatically on every GitHub push and pull request.

The result should provide a stable, self-describing edge contract for a later MATLAB `RemoteDevice` implementation.
