# Adding New Commands in MATLAB

This guide explains how to add a new command type to the MATLAB command system. The system uses a command-acknowledgment pattern where commands are sent to devices and acknowledgments are returned.

## Architecture Overview

The command system consists of:

1. **Base Classes**: `Command` (abstract) and `Ack` (concrete base)
2. **Command Classes**: Specific command implementations (e.g., `PropertyCommand`, `MethodCommand`)
3. **Ack Classes**: Specific acknowledgment implementations (e.g., `PropertyAck`, `MethodAck`)
4. **CommandDecoder**: Utility class for decoding acknowledgments from structs

## Step-by-Step Guide

### Step 1: Create Your Command Class

Create a new file `<YourCommand>Command.m` in the `+commands` folder. The class must inherit from `commands.Command`.

**Template:**

```matlab
classdef <YourCommand>Command < commands.Command
    % Brief description of what this command does
    
    properties
        % Add your command-specific properties here
        param1
        param2
    end
    
    methods
        function obj = <YourCommand>Command(param1, param2, id, ts)
            arguments
                param1
                param2
                id = char(java.util.UUID.randomUUID())
                ts = posixtime(datetime('now'))
            end
            
            % Call parent constructor with command type string
            obj@commands.Command('<command_type>', id, ts);
            
            % Set your properties
            obj.param1 = param1;
            obj.param2 = param2;
        end
        
        function data = toDict(obj)
            % Convert command to struct for serialization
            % Always call parent toDict first
            data = toDict@commands.Command(obj);
            
            % Add your command-specific fields
            data.param1 = obj.param1;
            data.param2 = obj.param2;
        end
        
        function ack = send(obj, clientService, timeout)
            % Send the command using the provided client service
            if nargin < 3
                timeout = 5;
            end
            
            % Send command and get response
            resp = clientService.sendCommand(obj.toDict(), timeout);
            
            % Extract response fields (with safe defaults)
            ok = false;
            if isfield(resp, 'ok')
                ok = resp.ok;
            end
            
            % Extract command-specific response fields
            result_field = [];
            if isfield(resp, 'result_field')
                result_field = resp.result_field;
            end
            
            error_msg = '';
            if isfield(resp, 'error')
                error_msg = resp.error;
            end
            
            commandId = obj.id;
            if isfield(resp, 'id')
                commandId = resp.id;
            end
            
            % Create and return the appropriate Ack
            ack = commands.<YourCommand>Ack(commandId, ok, result_field, error_msg);
        end
    end
end
```

**Key Points:**
- The command type string (e.g., `'property'`, `'method'`) must match what the server expects
- Use `arguments` block for input validation and default values
- Always call `toDict@commands.Command(obj)` first, then add your fields
- The `send()` method handles the client service interaction and creates the appropriate Ack

### Step 2: Create Your Acknowledgment Class

Create a new file `<YourCommand>Ack.m` in the `+commands` folder. The class must inherit from `commands.Ack`.

**Template:**

```matlab
classdef <YourCommand>Ack < commands.Ack
    % Acknowledgment for <your command> commands
    
    properties
        % Add your ack-specific properties here
        result_field
    end
    
    methods
        function obj = <YourCommand>Ack(commandId, ok, result_field, error)
            arguments
                commandId
                ok
                result_field
                error
            end
            
            % Call parent constructor with ack type string
            obj@commands.Ack(commandId, ok, '<command_type>', error);
            
            % Set your properties
            obj.result_field = result_field;
        end
        
        function data = toDict(obj)
            % Convert acknowledgment to struct for serialization
            % Always call parent toDict first
            data = toDict@commands.Ack(obj);
            
            % Add your ack-specific fields (only if successful)
            if obj.ok && ~isempty(obj.result_field)
                data.result_field = obj.result_field;
            end
        end
    end
end
```

**Key Points:**
- The ack type string should match the command type
- Only include result fields in `toDict()` when `ok` is true and the field is not empty
- Use `arguments` block for input validation

### Step 3: Update CommandDecoder

Add a case for your new acknowledgment type in `CommandDecoder.m`:

```matlab
function ack = decodeAck(data)
    % ... existing code ...
    
    switch ackType
        case 'property'
            % ... existing code ...
            
        case 'method'
            % ... existing code ...
            
        case '<command_type>'  % Add your new case
            result_field = [];
            if isfield(data, 'result_field')
                result_field = data.result_field;
            end
            ack = commands.<YourCommand>Ack(data.id, ok, result_field, error_msg);
            
        otherwise
            error('Unrecognized Ack');
    end
end
```

**Key Points:**
- Extract all ack-specific fields from the data struct
- Create the appropriate Ack instance with all required parameters

## Example: PropertyCommand and PropertyAck

Here's a complete example using the existing `PropertyCommand` and `PropertyAck`:

### PropertyCommand.m

```matlab
classdef PropertyCommand < commands.Command
    properties
        name
        value
    end
    
    methods
        function obj = PropertyCommand(name, value, id, ts)
            arguments
                name
                value
                id = char(java.util.UUID.randomUUID())
                ts = posixtime(datetime('now'))
            end
            
            obj@commands.Command('property', id, ts);
            obj.name = name;
            obj.value = value;
        end
        
        function data = toDict(obj)
            data = toDict@commands.Command(obj);
            data.name = obj.name;
            data.value = obj.value;
        end
        
        function ack = send(obj, clientService, timeout)
            if nargin < 3
                timeout = 5;
            end
            
            resp = clientService.sendCommand(obj.toDict(), timeout);
            
            ok = false;
            if isfield(resp, 'ok')
                ok = resp.ok;
            end
            
            respvalue = [];
            if isfield(resp, 'value')
                respvalue = resp.value;
            end
            
            error_msg = '';
            if isfield(resp, 'error')
                error_msg = resp.error;
            end
            
            commandId = obj.id;
            if isfield(resp, 'id')
                commandId = resp.id;
            end
            
            ack = commands.PropertyAck(commandId, ok, respvalue, error_msg);
        end
    end
end
```

### PropertyAck.m

```matlab
classdef PropertyAck < commands.Ack
    properties
        value
    end
    
    methods
        function obj = PropertyAck(commandId, ok, value, error)
            arguments
                commandId
                ok
                value
                error
            end
            
            obj@commands.Ack(commandId, ok, 'property', error);
            obj.value = value;
        end
        
        function data = toDict(obj)
            data = toDict@commands.Ack(obj);
            
            if obj.ok && ~isempty(obj.value)
                data.value = obj.value;
            end
        end
    end
end
```

## Command Types Reference

### Simple Commands (No Parameters)
- Example: `ReceiveCommand`
- Only inherits base properties (`id`, `type`, `ts`)
- `toDict()` just calls parent method

### Commands with Parameters
- Example: `PropertyCommand`, `MethodCommand`
- Add properties for command-specific data
- Override `toDict()` to include these properties

### Acknowledgments with Results
- Example: `PropertyAck` (returns `value`), `MethodAck` (returns `result`)
- Add result properties
- Include results in `toDict()` only when successful

### Acknowledgments without Results
- Example: Simple success/failure acks
- Can use base `Ack` class or create a minimal subclass
- Only include `ok` and `error` fields

## Best Practices

1. **Naming Convention**: 
   - Command class: `<Name>Command.m`
   - Ack class: `<Name>Ack.m`
   - Command type string: lowercase, descriptive (e.g., `'property'`, `'method'`)

2. **Error Handling**:
   - Always check for field existence before accessing (`isfield()`)
   - Provide safe defaults for missing fields
   - Extract `error` field even when `ok` is true (for warnings)

3. **Serialization**:
   - Always call parent `toDict()` first
   - Only include optional fields when they have meaningful values
   - For acks, only include result fields when `ok` is true

4. **UUID and Timestamps**:
   - Commands auto-generate UUIDs and timestamps if not provided
   - Use `char(java.util.UUID.randomUUID())` for IDs
   - Use `posixtime(datetime('now'))` for timestamps

5. **Testing**:
   - Test command creation with and without optional parameters
   - Test `toDict()` serialization
   - Test `send()` method with mock client service
   - Test ack decoding in `CommandDecoder`

## Python Reference

For reference, see `python/src/commands/commands.py` which implements the same command system in Python. The patterns are similar:
- Commands inherit from `Command` (abstract base class)
- Acks inherit from `Ack` base class
- Both have `to_dict()` methods for serialization
- Commands have `send()` methods that use `ClientService`

## Common Patterns

### Pattern 1: Command with Single Value Parameter
```matlab
% Command
obj = commands.PropertyCommand('frequency', 2.4e9);
data = obj.toDict();  % Includes: id, ts, type, name, value
ack = obj.send(clientService);  % Returns PropertyAck
```

### Pattern 2: Command with Multiple Parameters
```matlab
% Command
obj = commands.MethodCommand('configure', [1, 2, 3], struct('key', 'value'));
data = obj.toDict();  % Includes: id, ts, type, name, args, kwargs
ack = obj.send(clientService);  % Returns MethodAck
```

### Pattern 3: Simple Command (No Parameters)
```matlab
% Command
obj = commands.ReceiveCommand();
data = obj.toDict();  % Includes: id, ts, type
ack = obj.send(clientService);  % Returns ReceiveAck
```

## Troubleshooting

**Issue**: Command not recognized by server
- Check that command type string matches server expectations
- Verify `toDict()` includes all required fields

**Issue**: Ack decoding fails
- Ensure `CommandDecoder.decodeAck()` has a case for your ack type
- Verify ack type string matches command type

**Issue**: Missing fields in response
- Always use `isfield()` checks before accessing response fields
- Provide safe defaults for optional fields

**Issue**: Serialization errors
- Ensure all properties can be serialized to JSON
- Check that nested structs/objects are properly converted

