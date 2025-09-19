classdef MethodCommand < commands.Command
    % Command to call a method
    
    properties
        name
        args
        kwargs
    end
    
    methods
        function obj = MethodCommand(name, args, kwargs, id, ts)
            arguments
                name
                args = []
                kwargs = []
                id = char(java.util.UUID.randomUUID())
                ts = posixtime(datetime('now'))
            end
            
            obj@commands.Command('method', id, ts);
            obj.name = name;
            obj.args = args;
            obj.kwargs = kwargs;
        end
        
        function data = toDict(obj)
            % Convert command to struct for serialization
            data = toDict@commands.Command(obj);
            data.name = obj.name;
            data.args = obj.args;
            data.kwargs = obj.kwargs;
        end
        
        function ack = send(obj, clientService, timeout)
            % Send the command using the provided client service
            if nargin < 3
                timeout = 5;
            end
            
            resp = clientService.sendCommand(obj.toDict(), timeout);
            
            % Create MethodAck from response
            ok = false;
            if isfield(resp, 'ok')
                ok = resp.ok;
            end
            
            result = [];
            if isfield(resp, 'result')
                result = resp.result;
            end
            
            error_msg = '';
            if isfield(resp, 'error')
                error_msg = resp.error;
            end
            
            commandId = obj.id;
            if isfield(resp, 'id')
                commandId = resp.id;
            end
            
            ack = commands.MethodAck(commandId, ok, result, error_msg);
        end
    end
end
