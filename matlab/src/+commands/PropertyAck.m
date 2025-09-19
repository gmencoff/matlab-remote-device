classdef PropertyAck < commands.Ack
    % Acknowledgment for property commands
    
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
            % Convert acknowledgment to struct for serialization
            data = toDict@commands.Ack(obj);
            
            if obj.ok && ~isempty(obj.value)
                data.value = obj.value;
            end
        end
    end
end