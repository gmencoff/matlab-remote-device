classdef PropertyCommand < commands.Command
    % Command to set a property value
    
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
            % Convert command to struct for serialization
            data = toDict@commands.Command(obj);
            data.name = obj.name;
            data.value = obj.value;
        end
        
        function ack = send(obj, clientService, timeout)
            % Send the command using the provided client service
            if nargin < 3
                timeout = 5;
            end
            
            resp = clientService.sendCommand(obj.toDict(), timeout);
            
            % Create PropertyAck from response
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
