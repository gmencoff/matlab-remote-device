classdef FunctionCaller < handle

    % Call API functions for getting config and sending commands

    properties
        ConfigCallback
    end
    
    properties (Access = private)
        DeviceId
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
                % Make the HTTP request
                responseJson = webwrite(baseUrl, jsonPayload, options);
                
                % Parse the JSON response
                response = jsondecode(responseJson);
                
                % Check if successful
                if isfield(response, 'success') && response.success
                    ack = response.response;
                else
                    ack = commands.ErrorAck(cmd.id,response.error);
                end
                
            catch ME
                ack = commands.ErrorAck(cmd.id,ME.message);
            end
        end

        function pollConfig(obj)
            % Firebase function URL
            baseUrl = 'https://getconfig-tgyovhjiqq-uc.a.run.app';
            
            % Build the full URL with query parameter
            url = sprintf('%s?id=%s', baseUrl, obj.DeviceId);
            
            try
                % Make the HTTP GET request
                configData = webread(url);
                
                % Set the config
                obj.ConfigCallback(configData.data.config);
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
    end
end