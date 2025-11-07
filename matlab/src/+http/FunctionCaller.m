classdef FunctionCaller < handle

    % Call API functions for getting config and sending commands

    properties
        ConfigCallback
    end
    
    properties (Access = private)
        DeviceId
        RequestInProcess = false
    end

    methods
        function obj = FunctionCaller(deviceId)
            obj.DeviceId = deviceId;
        end

        function ack = sendCommand(obj,cmd,timeout)
            % Firebase function URL
            baseUrl = 'https://sendcommand-tgyovhjiqq-uc.a.run.app';

            % Prepare the JSON payload
            payload = struct();
            payload.deviceId = obj.DeviceId;
            payload.commandId = cmd.id;
            payload.command = cmd;
    
            % Convert to JSON string
            jsonPayload = jsonencode(payload);
    
            % Set up HTTP request
            options = weboptions(...
                'MediaType', 'application/json', ...
                'RequestMethod', 'POST', ...
                'Timeout', timeout, ...  % Slightly longer than function timeout
                'CharacterEncoding', 'UTF-8');
    
            try
                % Wait until no request is in process
                while obj.RequestInProcess
                    pause(0.01);
                end

                % Make the HTTP request
                obj.RequestInProcess = true;
                response = webwrite(baseUrl, jsonPayload, options);
                obj.RequestInProcess = false;
                
                % Check if successful
                if isfield(response, 'success') && response.success
                    ack = response.response;
                else
                    ack = commands.ErrorAck(cmd.id,response.error);
                end
                
            catch ME
                obj.RequestInProcess = false;
                ack = commands.ErrorAck(cmd.id,ME.message);
            end
        end

        function pollConfig(obj)
            if obj.RequestInProcess
                return
            end
            
            % Firebase function URL
            baseUrl = 'https://getconfig-tgyovhjiqq-uc.a.run.app';
            
            % Build the full URL with query parameter
            url = sprintf('%s?id=%s', baseUrl, obj.DeviceId);
            
            try
                % Make the HTTP GET request
                options = weboptions('Timeout', 60);
                configData = webread(url,options);
                
                % Set the config
                obj.ConfigCallback(configData.config);
            catch ME
                % Handle errors
                if contains(ME.message, '404')
                    error('Config not found: %s', configId);
                elseif contains(ME.message, '400')
                    error('Invalid request: Missing or invalid config ID');
                elseif contains(ME.message, '500')
                    error('Server error: Please try again later');
                else
                    error('Network error: %s', ME.message);
                end
            end
        end
        
        function topicData = getTopicData(obj, topicId, lastTimestamp)
            % Firebase function URL
            baseUrl = 'https://gettopicdata-tgyovhjiqq-uc.a.run.app';
            
            % Prepare the JSON payload
            payload = struct();
            payload.deviceId = obj.DeviceId;
            payload.topicId = topicId;
            payload.lastTimestamp = lastTimestamp;
            
            % Convert to JSON string
            jsonPayload = jsonencode(payload);
            
            % Set up HTTP request with longer timeout (65 seconds)
            % The server waits up to 60 seconds for new data
            options = weboptions(...
                'MediaType', 'application/json', ...
                'RequestMethod', 'POST', ...
                'Timeout', 65, ...
                'CharacterEncoding', 'UTF-8');
            
            try
                % Wait until no request is in process
                while obj.RequestInProcess
                    pause(0.01);
                end
                
                % Make the HTTP request
                obj.RequestInProcess = true;
                response = webwrite(baseUrl, jsonPayload, options);
                obj.RequestInProcess = false;
                
                % Return the topic data
                topicData = response;
                
            catch ME
                obj.RequestInProcess = false;
                
                % Handle specific errors
                if contains(ME.message, '404')
                    error('Topic not found or inactive');
                elseif contains(ME.message, '408')
                    error('Timeout waiting for topic data update');
                elseif contains(ME.message, '400')
                    error('Invalid request: Missing or invalid parameters');
                elseif contains(ME.message, '500')
                    error('Server error: Please try again later');
                else
                    error('Network error: %s', ME.message);
                end
            end
        end
    end
end