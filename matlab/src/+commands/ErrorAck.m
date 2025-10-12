classdef ErrorAck < commands.Ack
    %ERRORACK Summary of this class goes here
    %   Detailed explanation goes here

    properties
        Property1
    end

    methods
        function obj = ErrorAck(commandId, error)
            arguments
                commandId
                error
            end
            
            obj@commands.Ack(commandId, false, 'property', error);
        end
        
        function data = toDict(obj)
            % Convert acknowledgment to struct for serialization
            data = toDict@commands.Ack(obj);
        end
    end
end