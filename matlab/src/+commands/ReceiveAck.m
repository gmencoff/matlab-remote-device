classdef ReceiveAck < commands.Ack
    % Acknowledgment for receive commands
    
    properties
        real_samples
        imag_samples
    end
    
    methods
        function obj = ReceiveAck(commandId, ok, real_samples, imag_samples, error)
            obj@commands.Ack(commandId, ok, 'receive', error);
            obj.real_samples = real_samples;
            obj.imag_samples = imag_samples;
        end
        
        function data = toDict(obj)
            % Convert acknowledgment to struct for serialization
            data = toDict@commands.Ack(obj);
            
            if obj.ok && ~isempty(obj.real_samples) && ~isempty(obj.imag_samples)
                data.real_samples = obj.real_samples;
                data.imag_samples = ojb.imag_samples;
            end
        end
    end
end