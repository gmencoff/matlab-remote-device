classdef ReceiveStreamAck < commands.Ack
    % Acknowledgment for receive stream commands
    
    methods
        function obj = ReceiveStreamAck(commandId, ok, error)
            arguments
                commandId
                ok
                error = ''
            end
            
            obj@commands.Ack(commandId, ok, 'receive_stream', error);
        end
        
        function data = toDict(obj)
            % Convert acknowledgment to struct for serialization
            data = toDict@commands.Ack(obj);
        end
    end
end

