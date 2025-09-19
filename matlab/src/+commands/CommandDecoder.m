classdef CommandDecoder
    % Utility class for encoding/decoding commands and acknowledgments
    
    methods (Static)
        function ack = decodeAck(data)
            % Create an acknowledgment instance from a struct
            if ~isfield(data, 'id')
                error('Acknowledgment data missing id field');
            end
            
            ackType = 'generic';
            if isfield(data, 'type')
                ackType = data.type;
            end
            
            ok = false;
            if isfield(data, 'ok')
                ok = data.ok;
            end
            
            error_msg = '';
            if isfield(data, 'error')
                error_msg = data.error;
            end
            
            switch ackType
                case 'property'
                    value = [];
                    if isfield(data, 'value')
                        value = data.value;
                    end
                    ack = commands.PropertyAck(data.id, ok, value, error_msg);
                    
                case 'method'
                    result = [];
                    if isfield(data, 'result')
                        result = data.result;
                    end
                    ack = commands.MethodAck(data.id, ok, result, error_msg);
                    
                otherwise
                    error('Unrecognized Ack');
            end
        end
    end
end
