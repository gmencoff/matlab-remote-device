classdef WebsocketFunctionCaller < http.FunctionCaller
    
    % Function caller for websocket interface

    properties (Access = private)
        DeviceId
        FunctionUrls = http.WebsocketFunctionUrls
        ConfigCallback
        RequestInProcess
    end

    methods
        function obj = WebsocketFunctionCaller(deviceId)
            obj.DeviceId = deviceId;
        end

        function ack = sendCommand(obj,cmd,timeout)
            % Websocket function URL
            url = obj.FunctionUrls.SendCommand;

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
                'Timeout', timeout, ...
                'CharacterEncoding', 'UTF-8');
    
            try
                % Wait until no request is in process
                while obj.RequestInProcess
                    pause(0.01);
                end

                % Make the HTTP request
                obj.RequestInProcess = true;
                response = webwrite(url, jsonPayload, options);
                obj.RequestInProcess = false;
                
                % Check if successful
                if isfield(response, 'status') && strcmp(response.status,'ok')
                    ack = response.result;
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
            
            % Websocket function URL
            url = obj.FunctionUrls.GetConfig;

            % Prepare the JSON payload
            payload = struct();
            payload.deviceId = obj.DeviceId;
    
            % Convert to JSON string
            jsonPayload = jsonencode(payload);

            % Make the HTTP POST request
            options = weboptions(...
            'MediaType', 'application/json', ...
            'RequestMethod', 'POST', ...
            'Timeout', 10, ...
            'CharacterEncoding', 'UTF-8');
            
            try
                % Wait until no request is in process
                while obj.RequestInProcess
                    pause(0.01);
                end

                % Make the HTTP request
                obj.RequestInProcess = true;
                response = webwrite(url, jsonPayload, options);
                obj.RequestInProcess = false;
                
                % Set the config
                obj.ConfigCallback(response.config);
            catch ME
                obj.RequestInProcess = false;
                % Handle errors
                if contains(ME.message, '404')
                    error('Config not found: %s', obj.DeviceId);
                elseif contains(ME.message, '400')
                    error('Invalid request: Missing or invalid config ID');
                elseif contains(ME.message, '500')
                    error('Server error: Please try again later');
                else
                    error('Network error: %s', ME.message);
                end
            end
        end
        
        function topicData = getTopicData(~, ~, ~)
            % No-op
            topicData = [];
        end

        function setConfigCallback(obj,callback)
            obj.ConfigCallback = callback;
        end
    end
end