classdef MethodAck < commands.Ack
    % Acknowledgment for method commands
    
    properties
        result
    end
    
    methods
        function obj = MethodAck(commandId, ok, result, error)
            if nargin < 3
                result = [];
            end
            if nargin < 4
                error = '';
            end
            
            obj@commands.Ack(commandId, ok, 'method', error);
            obj.result = result;
        end
        
        function data = toDict(obj)
            % Convert acknowledgment to struct for serialization
            data = toDict@commands.Ack(obj);
            
            if obj.ok && ~isempty(obj.result)
                data.result = obj.result;
            end
        end
    end
end
