classdef HttpClientService < client.ClientService
    properties (Access = private)
        ConfigCallback
        DeviceId
        PollInterval
        ConfigTimer
    end

    methods
        function obj = HttpClientService(deviceId,optargs)
            arguments
                deviceId
                optargs.PollInterval = 10
            end
            
            obj.DeviceId = deviceId;
            obj.PollInterval = optargs.PollInterval;
        end
        
        function response = sendCommand(obj, cmd, timeout)
            % TODO
        end
        
        function subscribeConfig(obj, callback)
            % Poll config.json and invoke callback whenever it changes
            obj.ConfigCallback = callback;
            
            % Start polling timer
            obj.ConfigTimer = timer('ExecutionMode', 'fixedRate', ...
                                  'Period', obj.PollInterval, ...
                                  'TimerFcn', @(~,~)pollConfig(obj));
            start(obj.ConfigTimer);
        end

        function delete(obj)
            if ~isempty(obj.ConfigTimer)
                stop(obj.ConfigTimer);
            end
        end
    end
end

function pollConfig(obj)
            % Replace with your actual Firebase function URL
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