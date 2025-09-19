classdef Ack < handle
    % Base class for command acknowledgments
    
    properties
        id
        ok
        type
        error
        ts
    end
    
    methods
        function obj = Ack(commandId, ok, ackType, error)
            if nargin < 4
                error = '';
            end
            
            obj.id = commandId;
            obj.ok = ok;
            obj.type = ackType;
            obj.error = error;
            obj.ts = posixtime(datetime('now'));
        end
        
        function data = toDict(obj)
            % Convert acknowledgment to struct for serialization
            data = struct('id', obj.id, 'ok', obj.ok, 'ts', obj.ts, 'type', obj.type);
            
            if ~obj.ok && ~isempty(obj.error)
                data.error = obj.error;
            end
        end
    end
end
