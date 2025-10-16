classdef ReceiveCommand < commands.Command
      % Command to call a method
    
    properties
        name
        args
        kwargs
    end
    
    methods
        function obj = ReceiveCommand(id, ts)
            arguments
                id = char(java.util.UUID.randomUUID())
                ts = posixtime(datetime('now'))
            end
            
            obj@commands.Command('receive', id, ts);
        end
        
        function data = toDict(obj)
            % Convert command to struct for serialization
            data = toDict@commands.Command(obj);
        end
        
        function ack = send(obj, clientService, timeout)
            % Send the command using the provided client service
            if nargin < 3
                timeout = 5;
            end
            
            resp = clientService.sendCommand(obj.toDict(), timeout);
            
            % Create ReceiveAck from response
            ok = false;
            if isfield(resp, 'ok')
                ok = resp.ok;
            end
            
            real_samples = [];
            if isfield(resp, 'real_samples')
                real_samples = resp.real_samples;
            end

            imag_samples = [];
            if isfield(resp, 'imag_samples')
                imag_samples = resp.imag_samples;
            end
            
            error_msg = '';
            if isfield(resp, 'error')
                error_msg = resp.error;
            end
            
            commandId = obj.id;
            if isfield(resp, 'id')
                commandId = resp.id;
            end
            
            ack = commands.ReceiveAck(commandId, ok, real_samples, imag_samples, error_msg);
        end
    end
end
