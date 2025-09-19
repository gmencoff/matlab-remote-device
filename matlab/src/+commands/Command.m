classdef (Abstract) Command < handle
    % Base class for all commands
    
    properties
        id
        type
        ts
    end
    
    methods
        function obj = Command(type, id, ts)
            if nargin < 2 || isempty(id)
                id = char(java.util.UUID.randomUUID());
            end
            if nargin < 3 || isempty(ts)
                ts = posixtime(datetime('now'));
            end
            
            obj.id = id;
            obj.type = type;
            obj.ts = ts;
        end
        
        function data = toDict(obj)
            % Convert command to struct for serialization
            data = struct('id', obj.id, 'ts', obj.ts, 'type', obj.type);
        end
    end
end
