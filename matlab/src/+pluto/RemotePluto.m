classdef RemotePluto < handle
    % Remote Pluto client that communicates via a ClientService
    
    properties (Access = private)
        clientService
        state
    end
    
    methods
        function obj = RemotePluto(clientService)
            arguments
                clientService (1,1) client.ClientService
            end
            obj.clientService = clientService;
            obj.state = struct();
            obj.clientService.subscribeConfig(@obj.onConfigUpdate);
        end
        
        function value = get(obj, name)
            % Get a property value
            if isfield(obj.state, name)
                value = obj.state.(name);
            else
                error('No such property: %s', name);
            end
        end
        
        function set(obj, name, value)
            % Set a property value
            cmd = commands.PropertyCommand(name, value);
            response = obj.clientService.sendCommand(cmd, 500);
            
            if response.ok
                % Update internal state
                obj.state.(name) = response.value;
            else
                error('Failed to set %s: %s', name, response.error);
            end
        end
        
        function result = callMethod(obj, name, varargin)
            % Call a method on the remote device
            cmd = commands.MethodCommand(name, varargin);
            response = obj.clientService.sendCommand(cmd, 500);
            
            if response.ok
                result = response.result;
            else
                error('Failed to call %s: %s', name, response.error);
            end
        end
        
        function names = getPropertyNames(obj)
            % Get list of available property names
            names = fieldnames(obj.state);
        end
        
        function disp(obj)
            % Custom display method
            fprintf('RemotePluto with properties:\n');
            names = obj.getPropertyNames();
            for i = 1:length(names)
                fprintf('  %s: %s\n', names{i}, mat2str(obj.state.(names{i})));
            end
        end
    end
    
    methods (Access = private)
        function onConfigUpdate(obj, cfg)
            % Handle config updates from the client service
            obj.state = cfg;
        end
    end
end
