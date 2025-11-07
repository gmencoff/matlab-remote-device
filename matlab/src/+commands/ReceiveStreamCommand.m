classdef ReceiveStreamCommand < commands.Command
    % Command to stream receive I/Q samples from the device
    
    properties
        duration
    end
    
    methods
        function obj = ReceiveStreamCommand(duration, id, ts)
            arguments
                duration
                id = char(java.util.UUID.randomUUID())
                ts = posixtime(datetime('now'))
            end
            
            obj@commands.Command('receive_stream', id, ts);
            obj.duration = duration;
        end
        
        function data = toDict(obj)
            % Convert command to struct for serialization
            data = toDict@commands.Command(obj);
            data.duration = obj.duration;
        end
        
        function ack = send(obj, clientService, timeout)
            % Send the command using the provided client service
            if nargin < 3
                timeout = 5;
            end
            
            resp = clientService.sendCommand(obj.toDict(), timeout);
            
            % Create ReceiveStreamAck from response
            ok = false;
            if isfield(resp, 'ok')
                ok = resp.ok;
            end
            
            error_msg = '';
            if isfield(resp, 'error')
                error_msg = resp.error;
            end
            
            commandId = obj.id;
            if isfield(resp, 'id')
                commandId = resp.id;
            end
            
            ack = commands.ReceiveStreamAck(commandId, ok, error_msg);
        end
    end
end

