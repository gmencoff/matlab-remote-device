classdef RemotePluto < handle
    % Remote Pluto client that communicates via a ClientService
    
    properties (Access = private)
        clientService
        state
        rxStreamLastTimestamp = 0;
    end
    
    methods
        function obj = RemotePluto(id,inargs)
            arguments
                id
                inargs.ClientService = []
            end
            if isempty(inargs.ClientService)
                obj.clientService = http.HttpClientService(id);
            else
                obj.clientService = inargs.ClientService;
            end
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
        
        function result = rx(obj)
            cmd = commands.ReceiveCommand();
            response = obj.clientService.sendCommand(cmd, 500);
            result = response.real_samples + 1i*response.imag_samples;
        end

        function startRxStream(obj, duration)
            cmd = commands.ReceiveStreamCommand(duration);
            response = obj.clientService.sendCommand(cmd, 500);
        end

        function data = getStreamData(obj)
            data = obj.clientService.getTopicData('rx_stream', obj.rxStreamLastTimestamp);
            obj.rxStreamLastTimestamp = data.timestamp;
            return data.data;
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

        function names = getPropertyNames(obj)
            % Get list of available property names
            names = fieldnames(obj.state);
        end
    end
end
